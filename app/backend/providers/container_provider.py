from abc import ABC, abstractmethod
from typing import AsyncIterator, List
from app.backend.events.event import Event
from app.backend.models.container_proxy import ContainerProxy

class ContainerProvider(ABC):

    @abstractmethod
    async def get_container(self, id: str) -> ContainerProxy | None:
        pass
    
    @abstractmethod
    async def list_containers(self) -> List[ContainerProxy]:
        pass

    @abstractmethod
    async def restart_container(self, id: str):
        pass

    @abstractmethod
    async def get_logs(self, id: str, logs_amount:int) -> str:
        pass

    @abstractmethod
    def stream_events(self) -> AsyncIterator[Event] :
        pass