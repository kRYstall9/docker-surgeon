
from typing import AsyncIterator

from docker import DockerClient

from app.backend.events.event import Event
from app.backend.models.container_proxy import ContainerProxy
from app.backend.providers.container_provider import ContainerProvider


class DockerClientProvider(ContainerProvider):

    def __init__(self, client:DockerClient):
        self.client:DockerClient = client

    async def get_container(self, id: str):
        container = self.client.containers.get(id)
        return ContainerProxy.from_docker(container, self)

    async def list_containers(self):
        containers = self.client.containers(all=True)
        return list(ContainerProxy.from_docker(c, self) for c in containers)

    async def restart_container(self, id: str):
        container = self.client.containers.get(id)
        return container.restart()
    
    async def get_logs(self, id: str, logs_amount: int):
        return self.client.containers.get(id).logs(tail = logs_amount).decode('utf8', errors='ignore')
    
    async def stream_events(self) -> AsyncIterator[Event]:
        for raw in self.client.events(decode=True):
            id = ''

            if 'id' in raw:
                id = raw['id']
            elif 'Actor' in raw and 'ID' in raw['Actor']:
                id = raw['Actor']['ID']

            yield Event(
                type = raw.get("Action", ''),
                id = id,
                name=raw.get("Actor", {}).get("Attributes", {}).get("name", '')
            )