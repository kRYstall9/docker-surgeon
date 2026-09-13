from __future__ import annotations
import asyncio
from logging import Logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.backend.core import Config
    from app.backend.providers import ContainerProvider
    from app.backend.services import EventHandlerService
    from app.backend.events import Event

class MonitorService():
    ALLOWED_EVENT_TYPE = {"die", "oom", "health_status: unhealthy"}
    def __init__(self, client: ContainerProvider, config: Config, handler: EventHandlerService, logger: Logger):
        self.client = client
        self.config = config
        self.logger = logger
        self.handler = handler
        self.queue = asyncio.Queue(maxsize=500)
        self.workers: list[asyncio.Task] = []

    
    async def monitor(self):

        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(5)
        ]
        
        await asyncio.gather(
            self.monitor_events(),
            self.monitor_exited_containers()
        )
    
    async def monitor_exited_containers(self):
        """Periodically monitor exited containers and enqueue them for processing.
        Docker events cannot reliably detect containers that have already
        exited before the event monitor starts. This method periodically
        queries Docker for all containers with an ``exited`` status and
        creates an ``Event`` for each one.

        The blocking ``list_containers`` call is executed in a separate
        thread to avoid blocking the asyncio event loop. The check is
        repeated every 30 seconds.

        Any error occurring while retrieving or processing the containers
        is caught and logged, allowing the monitoring loop to continue.
        """
        while True:
            try:
                exited_containers = await asyncio.to_thread(self.client.list_containers, all=True, filters={"status": "exited"}) or []
                for ec in exited_containers:
                    self.logger.debug(f"Container: {ec.name} with status: {ec.status} will be processed soon")
                    event = Event(ec.status, ec.id, ec.name)
                    await self.queue.put(event)
            except Exception as e:
                self.logger.error(f"An error occured while retrieving exited containers. Error: {e}")
            finally:
                #This check will be performed every 30~ seconds
                await asyncio.sleep(30)

    async def monitor_events(self):
        """Monitor Docker events and enqueue events with allowed types.

        Continuously listens for events emitted by running containers and
        filters them according to ``ALLOWED_EVENT_TYPE``. Events with an
        unsupported type are ignored, while accepted events are added to
        the processing queue.

        If the queue is full, the event is dropped and a warning is logged.
        Errors raised while reading or processing an event are caught and
        logged without stopping the event-monitoring loop.
        """
        async for event in self.client.stream_events():
            try:
                if not any(event.type.startswith(x) for x in self.ALLOWED_EVENT_TYPE):
                    self.logger.debug(f"Skipping event {event.type} for container {event.container_name}")
                    continue
                
                if self.queue.full():
                    self.logger.warning(f"Event queue full, dropping event {event.type} for container {event.container_name}")
                    continue
                
                self.logger.debug(f"Inserting event {event.type} for container {event.container_name} into the event queue")
                await self.queue.put(event)
            except Exception as e:
                self.logger.error(f"An error occured while reading an event. Error: {e}")
                
    async def _worker(self, name:str):
        while True:
            event = await self.queue.get()

            if event is None:
                break
            
            try:
                await self.handler.handle(event)
            except Exception as e:
                self.logger.error(f"An error occured for worker {name}: {e}")
            finally:
                self.queue.task_done()

    async def stop(self):
        for _ in self.workers:
            await self.queue.put(None)

        for w in self.workers:
            w.cancel()
