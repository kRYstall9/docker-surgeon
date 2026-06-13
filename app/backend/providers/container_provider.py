from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, TYPE_CHECKING
from app.backend.events import Event

if TYPE_CHECKING:
    from app.backend.models import ContainerProxy

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