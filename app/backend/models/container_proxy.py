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
    def attrs(self) -> dict:
        return self._data.get("attrs", {})
    
    @property
    def state(self) -> dict:
        return self.attrs.get("State", {})
    
    @property
    def health(self) -> dict:
        return self.state.get("Health", {})
    
    @property
    def health_status(self) -> str:
        return self.health.get("Status", "unknown")

    @property
    def exit_code(self) -> str | None:
        return self.state.get("ExitCode")

    @property 
    def status(self) -> str:
        return self.state.get("Status", "unknown")
    
    @staticmethod
    def from_dict(dict, client: ContainerProvider):
        return ContainerProxy(dict, client)
    
    @staticmethod
    def from_docker(container: Container, client:ContainerProvider):
        return ContainerProxy(container.attrs, client)
    
    async def restart(self):
        await self._client.restart_container(self.id)
    
    async def logs(self, tail:int=10):
        return await self._client.get_logs(self.id, tail)
    
    async def reload(self):
        container = await self._client.get_container(self.id)

        if container is not None:
            self._data = container._data
    