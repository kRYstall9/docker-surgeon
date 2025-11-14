from docker import DockerClient, from_env
from app.backend.core.config import Config
from logging import Logger
from datetime import datetime
from time import sleep
from app.backend.schemas.container_schema import ContainerBase
from app.backend.schemas.crashed_container_schema import CrashedContainerBase
from app.backend.repositories.container_repository import ContainerRepository
from app.backend.repositories.crashed_container_repository import CrashedContainerRepository


############
#  CONSTS  #
############
LABEL_NAME:str = "com.monitor.depends.on"


def monitor_containers(config:Config, logger:Logger):
    
    client = from_env()
    if client is None:
        print("[ERROR] - Failed to connect to Docker daemon.")
        return
    
    try:
        containers = client.containers.list(True)
        container_create_list = [ContainerBase(name=container.name, cid=container.id) for container in containers]
        ContainerRepository.add_containers(container_create_list, logger)
    except Exception as e:
        logger.error(f"An error occured on saving containers to db: {e}")
   
    _watch_container_events(client, config.restart_policy, config.logs_amount, logger)

def _watch_container_events(client: DockerClient, restart_policy:any, logs_amount:int, logger:Logger):
    already_processed = set()
    in_progress = set()
    
    for event in client.events(decode=True):
        try:
            if event.get("Type") != "container":
                continue
            
            container_id = event['id'][:12]
            container_object = client.containers.get(container_id)
            
            if container_object is None:
                logger.warning(f"Container with ID {container_id} not found.")
                continue
            
            if _canBeRestarted(client, container_object, restart_policy, logger):
                containerStatusAndExitCode = _getContainerStatusAndExitCode(client, container_object)
                container_health_status = containerStatusAndExitCode["healthStatus"]
                container_exit_code = containerStatusAndExitCode["exitCode"]
                
                logger.info(f"Container: {container_object.name} | Status: {container_health_status} | Exit Code: {container_exit_code}. The container will be restarted including all its dependent containers")
                crashed_container = CrashedContainerBase(container_id=container_object.id, logs=container_object.logs(tail=logs_amount))
                CrashedContainerRepository.add_crashed_container(crashed_container, logger)
                _restart_with_graph(client, container_object, already_processed, in_progress, restart_policy, logger)

        except Exception as e:
            logger.error(f"Exception occurred: {e}")


def _build_dependency_graph(client: DockerClient) -> dict:
    graph = {}
    all_containers = client.containers.list(all=True)

    for container in all_containers:
        depends_on = container.labels.get(LABEL_NAME)
        if depends_on:
            parents = [name.strip() for name in depends_on.split(",")]
            for parent in parents:
                if parent not in graph:
                    graph[parent] = []
                graph[parent].append(container.name)

    return graph

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


def _restart_with_graph(client: DockerClient, unhealthy_container, already_processed: set, in_progress: set, restart_policy:any, logger: Logger):
    graph = _build_dependency_graph(client, restart_policy, logger)
    sorted_container_names = _topological_sort(graph)
    
    logger.debug(f"Graph: {graph}")
    logger.debug(f"Sorted container names: {sorted_container_names}")
    

    to_restart = [unhealthy_container.name]
    relevant = set(to_restart)

    for container_name in sorted_container_names:
        parents = [parent for parent, children in graph.items() if container_name in children]
        ct = client.containers.get(container_name)

        if any(parent in relevant for parent in parents) and _canBeRestarted(client, ct, restart_policy, logger, True):
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
            container = client.containers.get(container_name)
            logger.info(f"Restarting container {container.name} ({container.id[:12]})")
            
            if container.name in parents:
                timeout = 60
                container.restart()
                logger.debug(f"Dependent containers found for {container.name}. Waiting until it is either 'running' or 'healthy'")
                logger.debug(f"Waiting {timeout} seconds before aborting the restart operation")
                operationInitTime = datetime.now()
                while True:
                    if _parentSuccessfullyRestarted(client, container, logger):
                        logger.debug(f"{container.name} restarted successfully. Proceeding to restart his children")
                        restarted_parents.add(container.name)
                        break
                    if _operationTimedOut(operationInitTime, datetime.now(), timeout, logger):
                        logger.warning(f"{container.name} did not recover in time - skipping dependent containers")
                        break
                    sleep(2)
            else:
                parents_of_child = [p for p, children in graph.items() if container.name in children]
                
                if not parents_of_child:
                    logger.info(f"Container {container.name} has no parent dependencies - restarting independently.")
                    container.restart()
                    
                else:
                    parents_of_child.sort(key=lambda p: len(graph.get(p, [])), reverse=True)
                    unready_parents = [p for p in parents_of_child if p in to_restart and p not in restarted_parents]
                    
                    if unready_parents:
                        logger.warning(f"Skipping {container.name}: waiting for parent(s) {unready_parents}.")
                        pending_children.add(container.name)
                        continue
                    
                    logger.info(f"Restarting child {container.name} ({container.id[:12]}) - parent(s) ready")
                    container.restart()

            logger.info(f"Successfully restarted {container.name}")
            already_processed.add(container_name)
        except Exception as e:
            logger.error(f"Failed to restart {container_name}: {e}")
        finally:
            in_progress.discard(container_name)
    
    if pending_children:
        _retry_pending_children(client, pending_children, graph, restarted_parents, logger)
    

    in_progress.clear()
    already_processed.clear()
    

def _getContainerStatusAndExitCode(client, container):
    
    container = client.containers.get(container.name)
    
    container_health_status = container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
    container_exit_code = container.attrs.get("State", {}).get("ExitCode")
    container_real_status = container.attrs.get("State", {}).get("Status", "unknown")

    return {"healthStatus": container_health_status, "exitCode": container_exit_code, "realStatus": container_real_status}

def _canBeRestarted(client, container, restart_policy:any, logger: Logger, checkOnChildren:bool = False) -> bool:
    
    if container.name in restart_policy.get("excludedContainers", []):
        logger.debug(f"{container.name} won't be restarted due to the restart policy")
        return False
    
    containerStatusAndExitCode = _getContainerStatusAndExitCode(client, container)
    container_status = containerStatusAndExitCode["healthStatus"]
    container_exit_code = containerStatusAndExitCode["exitCode"]
    container_real_status = containerStatusAndExitCode["realStatus"]
    
    logger.debug(f"CONTAINER NAME: {container.name} | STATUS: {container_status} | CODE: {container_exit_code} | REALSTATUS: {container_real_status}")
    
    policy = restart_policy["statuses"].get(container_status, {}) or restart_policy["statuses"].get(container_real_status, {})
    
    isContainerUnhealthy: bool = container_real_status == "running" and container_status == "unhealthy"
    
    if not policy and not isContainerUnhealthy:
        if checkOnChildren:
            return True
        logger.debug(f"No policy found. Container {container.name} won't be restarted")
        return False
    
    excluded_exit_codes = policy.get("codesToExclude", [])
    
    logger.debug(f"POLICY EXCLUDED EXIT CODES: {excluded_exit_codes}")
    
    # Container has to pass any of these checks to be restarted:
    # 1) Container is unhealthy
    # 2) Container matches the user-defined state and the exit code is not defined as excluded
    # 3) The parent of this container has to be restarted
    
    if isContainerUnhealthy or container_exit_code not in excluded_exit_codes or checkOnChildren:
        logger.debug(f"{container.name} will be restarted soon")
        return True 
    
    return False

def _parentSuccessfullyRestarted(client, container, logger:Logger) -> bool:
    """
    Checks if the parent container has successfully restarted
    Args:
        container (any): The parent container on which the status has to be checked
    """
    
    containerStatuses = _getContainerStatusAndExitCode(client, container)
    # A container Health status is unknown when there's not healthcheck for it
    logger.debug(f"{container.name} statuses: {containerStatuses}")
    if (containerStatuses["healthStatus"] == "unknown" or containerStatuses["healthStatus"] == "healthy") and containerStatuses["realStatus"] == "running":
        return True
    
    return False

def _operationTimedOut(initialDate:datetime, endDate:datetime, timeout:int, logger:Logger) -> bool:
    """
    Checks if the operation time has exceeded the given timeout
    Args:
        initialDate (datetime): start of the operation
        endDate (datetime): the current time
        timeout (int): Seconds after which the timeout should occur
    """
    
    deltaSeconds = (endDate-initialDate).seconds
    if deltaSeconds >= timeout:
        logger.debug(f"Aborting operation due to timeout exceed. Time passed: {deltaSeconds}. Max allowed: {timeout}")
        return True
    
    return False

def _retry_pending_children(client: DockerClient, pending_children: list, graph: dict, restarted_parents: set, logger: Logger, max_retries: int = 1, delay: int = 10):
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

                container = client.containers.get(child_name)
                logger.info(f"Retrying restart for {child_name} — parent(s) ready.")
                container.restart()
                logger.info(f"Successfully restarted {child_name}")

            except Exception as e:
                logger.error(f"Retry failed for {child_name}: {e}")
                still_pending.append(child_name)

        pending_children = still_pending
        if pending_children:
            logger.debug(f"{len(pending_children)} child container(s) still pending. Waiting {delay}s before next retry.")
            sleep(delay)
        else:
            logger.info("All pending child containers have been restarted successfully.")

    if pending_children:
        logger.warning(f"Some child containers could not be restarted after {max_retries} retries: {pending_children}")

