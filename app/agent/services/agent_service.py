import asyncio
import json
from logging import Logger
from typing import AsyncIterator
from docker import DockerClient
from docker.models.containers import Container


class AgentService:
    def __init__(self, client: DockerClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def stream_events(self) -> AsyncIterator[str]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=250)
        loop = asyncio.get_running_loop()

        def _producer():
            try:
                for event in self.client.events(decode=True):
                    if event.get("Type") == "container":
                        try:
                            loop.call_soon_threadsafe(
                                queue.put_nowait,
                                event
                            )
                        except asyncio.QueueFull:
                            self.logger.warning("Event queue full, dropping event")
            except Exception as e:
                self.logger.error(f"Event stream error: {e}")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        asyncio.get_running_loop().run_in_executor(None, _producer)

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    def restart_container(self, id: str | None = None):
        try:
            if not id:
                raise ValueError("Either name or id must be provided")
            
            container = self.client.containers.get(id)
            container.restart()
        except Exception as e:
            raise RuntimeError(f"Error restarting container: {e}")

    def list_containers(self) -> list[dict]:
        try:
            containers = self.client.containers.list(all=True)
            return [self._serialize_container(container) for container in containers]
        except Exception as e:
            raise RuntimeError(f"Error listing containers: {e}")
        
    def get_container(self, id: str | None = None) -> dict:
        try:
            if id:
                container = self.client.containers.get(id)
            else:
                raise ValueError("Either name or id must be provided")
            
            return self._serialize_container(container)
        except Exception as e:
            raise RuntimeError(f"Error getting container: {e}")

    def get_logs(self, id: str | None = None, tail: int = 10) -> str:
        try:
            if not id:
                raise ValueError("Either name or id must be provided")
            
            container = self.client.containers.get(id)
            logs = container.logs(tail=tail).decode('utf-8', errors='ignore')
            return logs
        except Exception as e:
            raise RuntimeError(f"Error getting container logs: {e}")
        
    def _serialize_container(self, container: Container) -> dict:
        attrs = container.attrs
        
        return {
                "id": container.id,
                "name": container.name,
                "labels": container.labels,
                "state": attrs.get("State", {}),
                "health": attrs.get("State", {}).get("Health", {}),
                "health_status": attrs.get("State", {}).get("Health", {}).get("Status", "unknown"),
                "exit_code": attrs.get("State", {}).get("ExitCode"),
                "status": attrs.get("State", {}).get("Status", "unknown")
            }

