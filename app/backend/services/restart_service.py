import asyncio
from datetime import datetime
from time import time
from logging import Logger
from typing import List
from app.backend.models import ContainerProxy
from app.backend.providers import ContainerProvider

class RestartService:
    DOCKER_SURGEON_LABEL = "com.monitor.depends.on"
    
    def __init__(self, restart_policy: dict, client: ContainerProvider, logger: Logger):
        self.restart_policy = restart_policy
        self.logger = logger
        self.client = client
        self.in_progress = set()
        self.cache_graph_time_amount = 600
        self.graph = {}
        self.last_graph_load_time = 0
        self.lock = asyncio.Lock()

    async def can_be_restarted(
        self,
        container: ContainerProxy | None,
        check_on_children:bool = False
    ) -> bool:
        
        if container is None:
            return False
        
        if container.name in self.restart_policy.get("excludedContainers", []):
            self.logger.debug(f"{container.name} won't be restarted due to the restart policy")
            return False

        self.logger.debug(f"Container name: {container.name} | Status: {container.health_status} | Code: {container.exit_code} | Real Status: {container.status}")
        
        # Use health status, then fall back to real status if health is unknown/missing from policy
        
        policy = {} if self.restart_policy == {} else (self.restart_policy["statuses"].get(container.health_status, {}) or self.restart_policy["statuses"].get(container.status, {}))
        
        isContainerUnhealthy: bool = container.status == "running" and container.health_status == "unhealthy"
        
        if not policy and not isContainerUnhealthy:
            if check_on_children:
                return True # Allow children to be restarted if parent is being restarted
            self.logger.debug(f"No policy found. Container {container.name} won't be restarted")
            return False
        
        excluded_exit_codes = policy.get("codesToExclude", [])
        
        self.logger.debug(f"POLICY EXCLUDED EXIT CODES: {excluded_exit_codes}")
        
        # Container has to pass any of these checks to be restarted:
        # 1) Container is unhealthy
        # 2) Container matches the user-defined state and the exit code is not defined as excluded
        # 3) The parent of this container has to be restarted (checkOnChildren is True)
        
        if isContainerUnhealthy or container.exit_code not in excluded_exit_codes or check_on_children:
            self.logger.debug(f"{container.name} will be restarted soon")
            return True 
        
        return False
    
    def _build_dependency_graph(self, containers: List[ContainerProxy]) -> dict:
        graph = {}
        for container in containers:
            depends_on = container.labels.get(self.DOCKER_SURGEON_LABEL)
            name = container.name

            if depends_on:
                parents = [p.strip() for p in depends_on.split(",")]
                for parent in parents:
                    if parent not in graph:
                        graph[parent] = []
                    graph[parent].append(name)
        return graph
    
    def _topological_sort(self, graph: dict) -> list:
        already_visited = set()
        stack = []

        def visit(node):
            if node in already_visited:
                return
            already_visited.add(node)
            for child in graph.get(node, []):
                visit(child)
            stack.append(node)

        for node in graph:
            visit(node)

        return stack[::-1]  # Invert the results
    
    async def restart_with_graph(
        self,
        unhealthy_container: ContainerProxy | None
    ):
        
        if unhealthy_container is None:
            return
        
        containers = await self.client.list_containers()

        if self.graph == {} or ((time() - self.last_graph_load_time) > self.cache_graph_time_amount):
            self.graph = self._build_dependency_graph(containers)
            self.last_graph_load_time = time()

        sorted_container_names = self._topological_sort(self.graph)
        
        self.logger.debug(f"Graph: {self.graph}")
        self.logger.debug(f"Sorted container names: {sorted_container_names}")
        
        to_restart = [unhealthy_container.name]
        relevant = set(to_restart)

        for container_name in sorted_container_names:
            # Check if the current container's parent(s) are in the list of containers to be restarted
            parents = [parent for parent, children in self.graph.items() if container_name in children]
            
            # Check if the container actually exists before trying to get it
            try:
                ct = await self.client.get_container(container_name)
            except Exception:
                self.logger.debug(f"Dependent container {container_name} not found, skipping.")
                continue
            
            if ct is None:
                continue
            
            if any(parent in relevant for parent in parents) and await self.can_be_restarted(ct, check_on_children=True):
                to_restart.append(container_name)
                relevant.add(container_name)

        self.logger.debug(f"Containers to restart: {to_restart}")
        
        parents = set(self.graph.keys())
        restarted_parents = set()
        pending_children = set()
        
        for container_name in to_restart:
            async with self.lock:
                if container_name in self.in_progress:
                    continue
                self.in_progress.add(container_name)
            try:
                container = await self.client.get_container(container_name)
                if container is None:
                    self.logger.warning(f"Container {container_name} not found. Skipping restart")
                    continue

                self.logger.info(f"Restarting container {container.name} ({container.id[:12]})")
                
                if container.name in parents:
                    timeout = 60
                    await self.client.restart_container(container_name)
                    self.logger.debug(f"Dependent containers found for {container.name}. Waiting until it is either 'running' or 'healthy'")
                    self.logger.debug(f"Waiting {timeout} seconds before aborting the restart operation")
                    operationInitTime = datetime.now()
                    while True:
                        if await self._parentSuccessfullyRestarted(container):
                            self.logger.debug(f"{container.name} restarted successfully. Proceeding to restart his children")
                            restarted_parents.add(container.name)
                            break
                        if self._operationTimedOut(operationInitTime, datetime.now(), timeout):
                            self.logger.warning(f"{container.name} did not recover in time - skipping dependent containers")
                            break
                        await asyncio.sleep(2)
                else:
                    parents_of_child = [p for p, children in self.graph.items() if container.name in children]
                    
                    if not parents_of_child:
                        self.logger.info(f"Container {container.name} has no parent dependencies - restarting independently.")
                        await self.client.restart_container(container.id or container.name)            
                    else:
                        parents_of_child.sort(key=lambda p: len(self.graph.get(p, [])), reverse=True)
                        unready_parents = [p for p in parents_of_child if p in to_restart and p not in restarted_parents]
                        
                        if unready_parents:
                            self.logger.warning(f"Skipping {container.name}: waiting for parent(s) {unready_parents}.")
                            pending_children.add(container.name)
                            continue
                            
                        self.logger.info(f"Restarting child {container.name} ({container.id[:12]}) - parent(s) ready")
                        await self.client.restart_container(container.id or container.name)

                self.logger.info(f"Successfully restarted {container.name}")
            except Exception as e:
                self.logger.error(f"Failed to restart {container_name}: {e}")
            finally:
                async with self.lock:
                    self.in_progress.discard(container_name)
        
        if pending_children:
            await self._retry_pending_children(pending_children, restarted_parents)
        

        self.in_progress.clear()

    async def _parentSuccessfullyRestarted(
        self,
        container: ContainerProxy | None
    ) -> bool:
        """
        Checks if the parent container has successfully restarted
        """
        if container is None:
            self.logger.warning("Unable to check whether the container has been successfully restarted")
            return False
        
        self.logger.debug(f"Reloading container object with id {container.id or container.name}")
        container = await self.client.get_container(container.id or container.name)

        if container is None:
            self.logger.warning("Unable to check whether the container has been successfully restarted")
            return False

        # A container Health status is unknown when there's not healthcheck for it
        if (container.health_status in ["healthy", "unknown"]) and container.status == "running":
            return True
        
        return False

    def _operationTimedOut(
        self,
        initialDate: datetime, 
        endDate:datetime, 
        timeout:int
    ) -> bool:
        """
        Checks if the operation time has exceeded the given timeout
        """
        
        deltaSeconds = (endDate-initialDate).seconds
        if deltaSeconds >= timeout:
            self.logger.debug(f"Aborting operation due to timeout exceed. Time passed: {deltaSeconds}. Max allowed: {timeout}")
            return True
        
        return False
    
    async def _retry_pending_children(
        self,
        pending_children: set | list,
        restarted_parents: set, 
        max_retries: int = 1, 
        delay: int = 10,
    ):
        """
        Tries to restart pending children
        """
        self.logger.info(f"Retrying {len(pending_children)} skipped child container(s).")

        for attempt in range(1, max_retries + 1):
            if not pending_children:
                break

            self.logger.debug(f"Retry attempt {attempt}/{max_retries}")
            still_pending = []

            for child_name in pending_children:
                try:
                    parents_of_child = [p for p, children in self.graph.items() if child_name in children]
                    unready_parents = [p for p in parents_of_child if p not in restarted_parents]

                    if unready_parents:
                        self.logger.debug(f"{child_name} still waiting for parent(s): {unready_parents}")
                        still_pending.append(child_name)
                        continue

                    container = await self.client.get_container(child_name)
                    self.logger.info(f"Retrying restart for {child_name} — parent(s) ready.")
                    await self.client.restart_container(child_name)
                    self.logger.info(f"Successfully restarted {child_name}")

                except Exception as e:
                    self.logger.error(f"Retry failed for {child_name}: {e}")
                    still_pending.append(child_name)

            pending_children = still_pending
            if pending_children and attempt < max_retries:
                self.logger.debug(f"{len(pending_children)} child container(s) still pending. Waiting {delay}s before next retry.")
                await asyncio.sleep(delay)
            else:
                self.logger.info("All pending child containers have been restarted successfully.")

        if pending_children:
            self.logger.warning(f"Some child containers could not be restarted after {max_retries} retries: {pending_children}")