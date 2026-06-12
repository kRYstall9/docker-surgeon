import asyncio
from typing import Any
from docker import DockerClient, from_env
from app.agent.agent_client import AgentClient
from app.backend.core.config import Config
from logging import Logger
from datetime import datetime
from app.backend.models.container_proxy import ContainerProxy
from app.backend.schemas.crashed_container_schema import CrashedContainerBase
from app.backend.repositories.crashed_container_repository import CrashedContainerRepository
from app.backend.notifications.notification_manager import NotificationManager
from docker.models.containers import Container


############
#  CONSTS  #
############
LABEL_NAME:str = "com.monitor.depends.on"

def monitor_containers(
    config:Config, 
    logger:Logger, 
    is_agent:bool = False, 
    agent_client: AgentClient | None = None):
    
    client:Any = None
    
    if not is_agent:
        try:
            client = from_env()
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            return
    else:
        if agent_client is None:
            logger.error("Agent client is not initialized for monitoring.")
            return
        client = None
    
    asyncio.run(_watch_container_events(client, config.restart_policy, config.logs_amount, logger, is_agent, agent_client))

async def _watch_container_events(
    client: DockerClient | None, 
    restart_policy: Any, 
    logs_amount:int, 
    logger:Logger, 
    is_agent:bool = False,
    agent_client: AgentClient | None = None):
    
    already_processed = set()
    in_progress = set()
    event_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    workers = start_workers(
        queue=event_queue,
        agent_client=agent_client,
        already_processed=already_processed,
        client=client,
        in_progress=in_progress,
        is_agent=is_agent,
        logger=logger,
        logs_amount=logs_amount,
        restart_policy=restart_policy,
        workers_amount=5,
    )

    filters: dict = {
        "event": ["die", "oom", "health_status"],
        "type": "container"
    }

    try:
        if not is_agent and client is not None:
            for event in client.events(decode=True, filters=filters):
                await event_queue.put(event)
        else:
            if agent_client is None:
                logger.error("Agent client not initialized")
                return
            
            async for event in agent_client.stream_events(filters=filters):
                await event_queue.put(event)

    except Exception as e:
        logger.error(e)
        workers.clear()
        event_queue.empty()

def _topological_sort(graph: dict) -> list:
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

async def _restart_with_graph(
    client: DockerClient | None, 
    unhealthy_container, 
    already_processed: set, 
    in_progress: set, 
    restart_policy:Any, 
    logger: Logger, 
    is_agent: bool = False,
    agent_client: AgentClient | None = None):
    

    # At this point, if not running via agent, client must be set
    if not is_agent:
        assert client is not None, logger.warning("Docker client not initialized")
        containers = client.containers.list(all=True)
    else:
        assert agent_client is not None, logger.warning("Agent client not initialized")
        containers = [ContainerProxy(container) for container in await agent_client.list_containers()]
    graph = _build_dependency_graph(containers)
    sorted_container_names = _topological_sort(graph)
    
    logger.debug(f"Graph: {graph}")
    logger.debug(f"Sorted container names: {sorted_container_names}")
    
    to_restart = [unhealthy_container.name]
    relevant = set(to_restart)

    for container_name in sorted_container_names:
        # Check if the current container's parent(s) are in the list of containers to be restarted
        parents = [parent for parent, children in graph.items() if container_name in children]
        
        # Check if the container actually exists before trying to get it
        try:
            ct = await _get_container(client, name=container_name, is_agent=is_agent, agent_client=agent_client)
        except Exception:
            logger.debug(f"Dependent container {container_name} not found, skipping.")
            continue


        if any(parent in relevant for parent in parents) and await _canBeRestarted(ct, restart_policy, logger, check_on_children=True, is_agent=is_agent, agent_client=agent_client):
            to_restart.append(container_name)
            relevant.add(container_name)

    logger.debug(f"Containers to restart: {to_restart}")
    
    parents = set(graph.keys())
    restarted_parents = set()
    pending_children = set()
    
    for container_name in to_restart:
        if container_name in in_progress or container_name in already_processed:
            continue
        in_progress.add(container_name)
        try:
            container = await _get_container(client, name=container_name, is_agent=is_agent, agent_client=agent_client)
            logger.info(f"Restarting container {container.name} ({container.id[:12] if container.id is not None else ''})")
            
            if container.name in parents:
                timeout = 60
                await _restart_container(container, is_agent, agent_client)
                logger.debug(f"Dependent containers found for {container.name}. Waiting until it is either 'running' or 'healthy'")
                logger.debug(f"Waiting {timeout} seconds before aborting the restart operation")
                operationInitTime = datetime.now()
                while True:
                    if await _parentSuccessfullyRestarted(container, logger, is_agent=is_agent, agent_client=agent_client):
                        logger.debug(f"{container.name} restarted successfully. Proceeding to restart his children")
                        restarted_parents.add(container.name)
                        break
                    if _operationTimedOut(operationInitTime, datetime.now(), timeout, logger):
                        logger.warning(f"{container.name} did not recover in time - skipping dependent containers")
                        break
                    await asyncio.sleep(2)
            else:
                parents_of_child = [p for p, children in graph.items() if container.name in children]
                
                if not parents_of_child:
                    logger.info(f"Container {container.name} has no parent dependencies - restarting independently.")
                    await _restart_container(container, is_agent, agent_client)            
                else:
                    parents_of_child.sort(key=lambda p: len(graph.get(p, [])), reverse=True)
                    unready_parents = [p for p in parents_of_child if p in to_restart and p not in restarted_parents]
                    
                    if unready_parents:
                        logger.warning(f"Skipping {container.name}: waiting for parent(s) {unready_parents}.")
                        pending_children.add(container.name)
                        continue
                        
                    logger.info(f"Restarting child {container.name} ({container.id[:12]}) - parent(s) ready")
                    await _restart_container(container, is_agent, agent_client)

            logger.info(f"Successfully restarted {container.name}")
            already_processed.add(container_name)
        except Exception as e:
            logger.error(f"Failed to restart {container_name}: {e}")
        finally:
            in_progress.discard(container_name)
    
    if pending_children:
        await _retry_pending_children(client, pending_children, graph, restarted_parents, logger, is_agent= is_agent, agent_client=agent_client)
    

    in_progress.clear()
    already_processed.clear()

async def _getContainerStatusAndExitCode(container, logger: Logger, is_agent: bool = False, agent_client:AgentClient | None = None, ) -> dict:
    
    # Reload container object to get the latest state
    if not is_agent:
        container.reload()
    else:
        container = ContainerProxy(await agent_client.get_container(name=container.name))
    
    attrs = container.attrs or {}
    container_health_status = attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
    container_exit_code = attrs.get("State", {}).get("ExitCode")
    container_real_status = attrs.get("State", {}).get("Status", "unknown")

    return {"healthStatus": container_health_status, "exitCode": container_exit_code, "realStatus": container_real_status}

async def _canBeRestarted(
    container, 
    restart_policy:any, 
    logger: Logger, 
    check_on_children:bool = False,
    is_agent: bool = False,
    agent_client: AgentClient | None = None) -> bool:
    
    if container.name in restart_policy.get("excludedContainers", []):
        logger.debug(f"{container.name} won't be restarted due to the restart policy")
        return False
    
    containerStatusAndExitCode = await _getContainerStatusAndExitCode(container, logger, is_agent=is_agent, agent_client=agent_client)
    container_status = containerStatusAndExitCode["healthStatus"]
    container_exit_code = containerStatusAndExitCode["exitCode"]
    container_real_status = containerStatusAndExitCode["realStatus"]
    
    logger.debug(f"CONTAINER NAME: {container.name} | STATUS: {container_status} | CODE: {container_exit_code} | REALSTATUS: {container_real_status}")
    
    # Use health status, then fall back to real status if health is unknown/missing from policy
    
    policy = {} if restart_policy == {} else (restart_policy["statuses"].get(container_status, {}) or restart_policy["statuses"].get(container_real_status, {}))
    
    isContainerUnhealthy: bool = container_real_status == "running" and container_status == "unhealthy"
    
    if not policy and not isContainerUnhealthy:
        if check_on_children:
            return True # Allow children to be restarted if parent is being restarted
        logger.debug(f"No policy found. Container {container.name} won't be restarted")
        return False
    
    excluded_exit_codes = policy.get("codesToExclude", [])
    
    logger.debug(f"POLICY EXCLUDED EXIT CODES: {excluded_exit_codes}")
    
    # Container has to pass any of these checks to be restarted:
    # 1) Container is unhealthy
    # 2) Container matches the user-defined state and the exit code is not defined as excluded
    # 3) The parent of this container has to be restarted (checkOnChildren is True)
    
    if isContainerUnhealthy or container_exit_code not in excluded_exit_codes or check_on_children:
        logger.debug(f"{container.name} will be restarted soon")
        return True 
    
    return False

async def _parentSuccessfullyRestarted(
    container, 
    logger:Logger,
    is_agent: bool = False,
    agent_client: AgentClient | None = None) -> bool:
    """
    Checks if the parent container has successfully restarted
    """
    
    containerStatuses = await _getContainerStatusAndExitCode(container, logger, is_agent=is_agent, agent_client=agent_client)
    # A container Health status is unknown when there's not healthcheck for it
    logger.debug(f"{container.name} statuses: {containerStatuses}")
    if (containerStatuses["healthStatus"] == "unknown" or containerStatuses["healthStatus"] == "healthy") and containerStatuses["realStatus"] == "running":
        return True
    
    return False

def _operationTimedOut(
    initialDate:datetime, 
    endDate:datetime, 
    timeout:int, 
    logger:Logger) -> bool:
    """
    Checks if the operation time has exceeded the given timeout
    """
    
    deltaSeconds = (endDate-initialDate).seconds
    if deltaSeconds >= timeout:
        logger.debug(f"Aborting operation due to timeout exceed. Time passed: {deltaSeconds}. Max allowed: {timeout}")
        return True
    
    return False

async def _retry_pending_children(
    client: DockerClient, 
    pending_children: list, 
    graph: dict, 
    restarted_parents: set, 
    logger: Logger, 
    max_retries: int = 1, 
    delay: int = 10,
    is_agent: bool = False,
    agent_client: AgentClient | None = None):
    """
    Tries to restart pending children
    """
    logger.info(f"Retrying {len(pending_children)} skipped child container(s).")

    for attempt in range(1, max_retries + 1):
        if not pending_children:
            break

        logger.debug(f"Retry attempt {attempt}/{max_retries}")
        still_pending = []

        for child_name in pending_children:
            try:
                parents_of_child = [p for p, children in graph.items() if child_name in children]
                unready_parents = [p for p in parents_of_child if p not in restarted_parents]

                if unready_parents:
                    logger.debug(f"{child_name} still waiting for parent(s): {unready_parents}")
                    still_pending.append(child_name)
                    continue

                container = await _get_container(client, name=child_name, is_agent=is_agent, agent_client=agent_client)
                logger.info(f"Retrying restart for {child_name} — parent(s) ready.")
                await _restart_container(container, is_agent=is_agent, agent_client=agent_client)
                logger.info(f"Successfully restarted {child_name}")

            except Exception as e:
                logger.error(f"Retry failed for {child_name}: {e}")
                still_pending.append(child_name)

        pending_children = still_pending
        if pending_children and attempt < max_retries:
            logger.debug(f"{len(pending_children)} child container(s) still pending. Waiting {delay}s before next retry.")
            await asyncio.sleep(delay)
        else:
            logger.info("All pending child containers have been restarted successfully.")

    if pending_children:
        logger.warning(f"Some child containers could not be restarted after {max_retries} retries: {pending_children}")

def _build_dependency_graph(containers) -> dict:
    graph = {}
    for container in containers:
        if isinstance(container, (dict, ContainerProxy)):
            depends_on = (container.get("labels") or {}).get(LABEL_NAME) or (container.get("Labels") or {}).get(LABEL_NAME)
            name = container.get("name") or container.get("Name")
        else:
            depends_on = container.labels.get(LABEL_NAME)
            name = container.name
        
        if depends_on:
            parents = [p.strip() for p in depends_on.split(",")]
            for parent in parents:
                if parent not in graph:
                    graph[parent] = []
                graph[parent].append(name)
    return graph

async def _restart_container(container, is_agent: bool = False, agent_client: AgentClient | None = None):
    if not is_agent:
        container.restart()
    else:
        await agent_client.restart_container(name=container.name)

async def _get_container(client, name: str | None = None, id: str | None = None, is_agent: bool = False, agent_client: AgentClient | None = None) -> ContainerProxy | Container:
    try:
        if not is_agent:
            return client.containers.get(name) if name else client.containers.get(id)
        else:
            container = await agent_client.get_container(name=name, id=id)
            return ContainerProxy(container)  # Wrap the container data in a proxy for attribute access
    except Exception as e:
        raise RuntimeError(f"Error getting container: {e}")
    
async def _get_container_logs(client, name: str | None = None, id: str | None = None, tail: int = 10, is_agent: bool = False, agent_client: AgentClient | None = None) -> str:
    try:
        if not is_agent:
            container = await _get_container(client, name, id, is_agent, agent_client)
            return container.logs(tail=tail).decode('utf-8', errors='ignore')
        else:
            return await agent_client.get_container_logs(name=name, id=id, tail=tail)
    except Exception as e:
        raise RuntimeError(f"Error getting container logs: {e}")

async def _process_event(event, logger: Logger, restart_policy:Any, logs_amount:int, already_processed:set, in_progress:set, client: DockerClient | None = None, is_agent: bool = False, agent_client: AgentClient | None = None):
    try:
        if event.get("Type") != "container":
            return
        
        container_id = None
        
        # --- FIX: Safely retrieve container ID ---
        # 1. Try to get the standard top-level ID
        if 'id' in event:
            container_id = event['id']
        
        # 2. If the standard ID is missing, check the Actor ID (common for exec/healthcheck events)
        elif 'Actor' in event and 'ID' in event['Actor']:
            container_id = event['Actor']['ID']
        # ----------------------------------------
        
        if container_id is None:
            logger.debug(f"Skipping container event with no ID: {event.get('Action')}")
            return
        
        container_id = container_id[:12] # Truncate to short ID
        container_object = await _get_container(client, id=container_id, is_agent=is_agent, agent_client=agent_client)
        
        if container_object is None:
            logger.warning(f"Container with ID {container_id} not found.")
            return
        
        if await _canBeRestarted(container_object, restart_policy, logger, is_agent=is_agent, agent_client=agent_client):
            containerStatusAndExitCode = await _getContainerStatusAndExitCode(container_object, logger, is_agent=is_agent, agent_client=agent_client)
            container_health_status = containerStatusAndExitCode["healthStatus"]
            container_exit_code = containerStatusAndExitCode["exitCode"]
            
            logger.info(f"Container: {container_object.name} | ID: {container_id} | Status: {container_health_status} | Exit Code: {container_exit_code}. The container will be restarted including all its dependent containers")
            logs = await _get_container_logs(client, id=container_id, tail=logs_amount, is_agent=is_agent, agent_client=agent_client)
            crashed_container = CrashedContainerBase(container_id=container_id, container_name=container_object.name, logs=logs)
            CrashedContainerRepository.add_crashed_container(crashed_container, logger)
            NotificationManager.container_crashed_event(container_name=container_object.name or '', container_logs=logs, container_exit_code=container_exit_code)
            await _restart_with_graph(client, container_object, already_processed, in_progress, restart_policy, logger, is_agent=is_agent, agent_client=agent_client)

    except Exception as e:
        # Added logging of the full event for easier debugging of new issues
        logger.error(f"Exception occurred: {e}. Event data: {event}")

async def worker(name: str, queue: asyncio.Queue, logger: Logger, restart_policy: Any, client: DockerClient | None, agent_client: AgentClient | None, is_agent: bool, already_processed:set, in_progress:set, logs_amount: int = 10):

    while True:
        event = await queue.get()
        try:
            await _process_event(
                event,
                logger,
                restart_policy,
                logs_amount,
                already_processed,
                in_progress,
                client,
                is_agent,
                agent_client
            )
        except Exception as e:
            logger.error(f"Worker {name} error: {e}")
        finally:
            queue.task_done()

def start_workers(queue: asyncio.Queue, logger: Logger, restart_policy: Any, client: DockerClient | None, agent_client: AgentClient | None, is_agent: bool, already_processed:set, in_progress:set, logs_amount: int = 10, workers_amount: int = 5):
    workers = []
    for i in range(workers_amount):
        workers.append(
            asyncio.create_task(
                worker(
                    name= f"worker-{i}",
                    queue=queue,
                    logger=logger,
                    restart_policy=restart_policy,
                    client=client,
                    agent_client=agent_client,
                    is_agent=is_agent,
                    already_processed=already_processed,
                    in_progress=in_progress,
                    logs_amount=logs_amount
                )
            )
        )

    return workers

