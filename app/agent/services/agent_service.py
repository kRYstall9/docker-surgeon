import json
from logging import Logger
from docker import DockerClient


def getEvents(client: DockerClient, logger: Logger):
    if(client is None):
        raise ValueError("Docker client is not initialized")
    try:
        events = client.events(decode=True)
        for event in events:
            if event.get("Type") == "container":
                yield json.dumps(event) + "\n\n"
    except Exception as e:
        logger.error(f"Error while streaming events: {e}")
        return

def restartContainer(client: DockerClient, name: str):
    try:
        container = client.containers.get(name)
        container.restart()
        return {"status": "restarted", "id": container.id, "name": container.name}
    except Exception as e:
        raise RuntimeError(f"Error restarting container: {e}")

def getContainers(client: DockerClient):
    try:
        containers = client.containers.list(all=True)
        return [{"id": c.id, "name": c.name, "status": c.status, "labels": c.labels} for c in containers]
    except Exception as e:
        raise RuntimeError(f"Error listing containers: {e}")