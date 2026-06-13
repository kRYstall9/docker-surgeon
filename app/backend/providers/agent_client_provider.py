from typing import AsyncIterator

from app.agent import AgentClient
from app.backend.events import Event
from app.backend.models import ContainerProxy
from app.backend.providers import ContainerProvider


class AgentClientProvider(ContainerProvider):

    def __init__(self, client:AgentClient):
        self.client:AgentClient = client

    async def get_container(self, id: str):
        container = await self.client.get_container(id)
        return ContainerProxy.from_dict(dict= container, client=self)

    async def list_containers(self):
        containers = await self.client.list_containers()
        return list(ContainerProxy.from_dict(c, self) for c in containers)

    async def restart_container(self, id: str):
        await self.client.restart_container(id)
    
    async def get_logs(self, id: str, logs_amount: int):
        return await self.client.get_container_logs(id, logs_amount)
    
    async def stream_events(self) -> AsyncIterator[Event]:
        async for raw in self.client.stream_events():
            id = ''

            if 'id' in raw:
                id = raw['id']
            elif 'Actor' in raw and 'ID' in raw['Actor']:
                id = raw['Actor']['ID']

            yield Event(
                type = raw.get("Action", ''),
                id = id,
                name = raw.get("Actor", {}).get("Attributes", {}).get("name", "")
            )