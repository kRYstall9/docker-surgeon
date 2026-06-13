import asyncio
import json
from logging import Logger
from docker import DockerClient
from docker.models.containers import Container


async def getEvents(client: DockerClient, logger: Logger):
    if client is None:
        raise ValueError("Docker client is not initialized")
    
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def _stream():
        try:
            for event in client.events(decode=True):
                if event.get("Type") == "container":
                    loop.call_soon_threadsafe(queue.put_nowait, json.dumps(event))
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, None)
            logger.error(f"Error while streaming events: {e}")

    loop.run_in_executor(None, _stream)

    while True:
        item = await queue.get()
        if item is None:
            break
        yield f"data: {item}\n\n"

def restartContainer(client: DockerClient, id: str | None = None):
    try:
        if not id:
            raise ValueError("Either name or id must be provided")
        
        container = client.containers.get(id)
        container.restart()
    except Exception as e:
        raise RuntimeError(f"Error restarting container: {e}")

def getContainers(client: DockerClient) -> list[dict]:
    try:
        containers = client.containers.list(all=True)
        return [_serialize_container(container) for container in containers]
    except Exception as e:
        raise RuntimeError(f"Error listing containers: {e}")
    
def getContainer(client: DockerClient, id: str | None = None) -> dict:
    try:
        if id:
            container = client.containers.get(id)
        else:
            raise ValueError("Either name or id must be provided")
        
        return _serialize_container(container)
    except Exception as e:
        raise RuntimeError(f"Error getting container: {e}")

def getContainerLogs(client: DockerClient, id: str | None = None, tail: int = 10) -> str:
    try:
        if not id:
            raise ValueError("Either name or id must be provided")
        
        container = client.containers.get(id)
        logs = container.logs(tail=tail).decode('utf-8', errors='ignore')
        return logs
    except Exception as e:
        raise RuntimeError(f"Error getting container logs: {e}")
    
def _serialize_container(container: Container) -> dict:
    return {
        "id": container.id,
        "short_id": container.short_id,
        "name": container.name,
        "status": container.status,
        "labels": container.labels,
        "attrs": container.attrs
    }