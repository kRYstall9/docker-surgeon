import asyncio
from app.backend.core import Config
from logging import Logger
from app.backend.providers import ContainerProvider
from app.backend.services import EventHandlerService


class MonitorService():
    ALLOWED_EVENT_TYPE = {"die", "oom", "health_status: unhealthy"}
    def __init__(self, client: ContainerProvider, config: Config, handler: EventHandlerService, logger: Logger):
        self.client = client
        self.config = config
        self.logger = logger
        self.handler = handler
        self.queue = asyncio.Queue(maxsize=100)
        self.workers: list[asyncio.Task] = []

    
    async def monitor(self):

        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(5)
        ]

        async for event in self.client.stream_events():
            try:
                if not any(event.type.startswith(x) for x in self.ALLOWED_EVENT_TYPE):
                    self.logger.debug(f"Skipping event {event.type}")
                    continue
                
                if self.queue.full():
                    self.logger.warning("Event queue full, dropping event")
                    continue

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