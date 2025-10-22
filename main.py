import docker
from docker import DockerClient
from dotenv import load_dotenv
import os
import json
import logging
from logging import Logger
import pytz
from datetime import datetime

load_dotenv()

############
#  CONSTS  #
############
LABEL_NAME:str = "com.monitor.depends.on"


def monitor_containers():
    client = docker.from_env()
    if client is None:
        print("[ERROR] - Failed to connect to Docker daemon.")
        return
    
    restart_policy = os.getenv("RESTART_POLICY")
    restart_policy = json.loads(restart_policy)
    
    logger = getLogger()
    
    logger.info("Connected to Docker daemon.")
    logger.info(f"Restarting on: unhealthy,{','.join(restart_policy.get('statuses', {}))}")
    logger.info(f"Excluded containers: {','.join(restart_policy.get('excludedContainers', []))}")

    watch_container_events(client, restart_policy, logger)

def getLogger() -> Logger:
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    log_timezone = os.getenv("LOG_TIMEZONE", "UTC")
    
    try:
        tz = pytz.timezone(log_timezone)
    except Exception as e:
        tz = pytz.UTC
        logging.warning(f"Timezone '{log_timezone}' not valid. Using UTC")
        
    def time_in_tz(*args):
        return datetime.now(tz).timetuple()
    
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logger.propagate = False
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - Func: %(funcName)s - [MSG]: %(message)s')
    formatter.converter = time_in_tz
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def watch_container_events(client: DockerClient, restart_policy:any, logger:Logger):
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
            
            if _canBeRestarted(container_object, restart_policy, logger):
                containerStatusAndExitCode = _getContainerStatusAndExitCode(container_object)
                container_health_status = containerStatusAndExitCode["healthStatus"]
                container_exit_code = containerStatusAndExitCode["exitCode"]
                
                logger.info(f"Container: {container_object.name} | Status: {container_health_status} | Exit Code: {container_exit_code}. The container will be restarted including all its dependent containers")
                restart_with_graph(client, container_object, already_processed, in_progress, restart_policy, logger)

        except Exception as e:
            logger.error(f"Exception occurred: {e}")


def build_dependency_graph(client: DockerClient, restart_policy:any, logger:Logger) -> dict:
    graph = {}
    all_containers = client.containers.list(all=True)

    for container in all_containers:
        
        if _canBeRestarted(container, restart_policy, logger):
            depends_on = container.labels.get(LABEL_NAME)
            if depends_on:
                parents = [name.strip() for name in depends_on.split(",")]
                for parent in parents:
                    if parent not in graph:
                        graph[parent] = []
                    graph[parent].append(container.name)

    return graph

def topological_sort(graph: dict) -> list:
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


def restart_with_graph(client: DockerClient, unhealthy_container, already_processed: set, in_progress: set, restart_policy:any, logger: Logger):
    graph = build_dependency_graph(client, restart_policy, logger)
    sorted_container_names = topological_sort(graph)
    
    logger.debug(f"Graph: {graph}")
    logger.debug(f"Sorted container names: {sorted_container_names}")
    

    to_restart = [unhealthy_container.name]
    relevant = set(to_restart)

    for container_name in sorted_container_names:
        parents = [parent for parent, children in graph.items() if container_name in children]
        if any(parent in relevant for parent in parents):
            to_restart.append(container_name)
            relevant.add(container_name)

    logger.debug(f"Containers to restart: {to_restart}")
    
    for container_name in to_restart:
        if container_name in in_progress or container_name in already_processed:
            continue
        in_progress.add(container_name)
        try:
            container = client.containers.get(container_name)
            logger.info(f"Restarting container {container.name} ({container.id[:12]})")
            container.restart()
            logger.info(f"Successfully restarted {container.name}")
            already_processed.add(container_name)
        except Exception as e:
            logger.error(f"Failed to restart {container_name}: {e}")
        finally:
            in_progress.discard(container_name)

    in_progress.clear()
    already_processed.clear()
    

def _getContainerStatusAndExitCode(container):
    container_health_status = container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
    container_exit_code = container.attrs.get("State", {}).get("ExitCode")
    container_real_status = container.attrs.get("State", {}).get("Status", "unknown")

    return {"healthStatus": container_health_status, "exitCode": container_exit_code, "realStatus": container_real_status}

def _canBeRestarted(container, restart_policy:any, logger: Logger) -> bool:
    
    if container.name in restart_policy.get("excludedContainers", []):
        logger.debug(f"{container.name} won't be restarted due to the restart policy")
        return False
    
    containerStatusAndExitCode = _getContainerStatusAndExitCode(container)
    container_status = containerStatusAndExitCode["healthStatus"]
    container_exit_code = containerStatusAndExitCode["exitCode"]
    container_real_status = containerStatusAndExitCode["realStatus"]
    
    logger.debug(f"CONTAINER NAME: {container.name} | STATUS: {container_status} | CODE: {container_exit_code} | REALSTATUS: {container_real_status}")
    
    policy = restart_policy["statuses"].get(container_status, {}) or restart_policy["statuses"].get(container_real_status, {})
    
    if not policy:
        return False
    
    excluded_exit_codes = policy.get("codesToExclude", [])
    
    logger.debug(f"POLICY EXCLUDED EXIT CODES: {excluded_exit_codes}")
    
    isContainerUnhealthy: bool = container_real_status == "running" and container_status == "unhealthy"
    
    if isContainerUnhealthy or (container_real_status == "exited" and container_exit_code not in excluded_exit_codes):
        logger.debug(f"{container.name} will be restarted soon")
        return True 
    
    return False
    


if __name__ == "__main__":
    monitor_containers()
