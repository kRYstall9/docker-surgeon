from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.backend.providers import ContainerProvider
    
from docker.models.containers import Container


class ContainerProxy:
    def __init__(self, data: dict, client: ContainerProvider):
        self._data = data
        self._client = client

    @property
    def id(self) -> str:
        return self._data.get("id", '')
    
    @property
    def name(self):
        return self._data.get("name", '')
    
    @property
    def labels(self):
        return self._data.get("labels", {})
  
    @property
    def state(self) -> dict:
        return self._data.get("state", {})
    
    @property
    def health(self) -> dict:
        return self._data.get("health", {})
    
    @property
    def health_status(self) -> str:
        return self._data.get("health_status", "unknown")

    @property
    def exit_code(self) -> str | None:
        return self._data.get("exit_code")

    @property 
    def status(self) -> str:
        return self._data.get("status", "unknown")
    
    @staticmethod
    def from_dict(dict, client: ContainerProvider):
        return ContainerProxy(dict, client)
    
    @staticmethod
    def from_docker(container: Container, client:ContainerProvider):
        attrs = container.attrs

        return ContainerProxy(
            data = {
                "id": container.id,
                "name": container.name,
                "labels": container.labels,
                "state": attrs.get("State", {}),
                "health": attrs.get("State", {}).get("Health", {}),
                "health_status": attrs.get("State", {}).get("Health", {}).get("Status", "unknown"),
                "exit_code": attrs.get("State", {}).get("ExitCode"),
                "status": attrs.get("State", {}).get("Status", "unknown")
            }, 
            client=client
        )
    
    async def restart(self):
        await self._client.restart_container(self.id)
    
    async def logs(self, tail:int=10):
        return await self._client.get_logs(self.id, tail)
    
    async def reload(self):
        container = await self._client.get_container(self.id)

        if container is not None:
            self._data = container._data
    