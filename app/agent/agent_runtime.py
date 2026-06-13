import asyncio
from logging import Logger

from app.backend.core.config import Config
from app.backend.providers.container_provider import ContainerProvider
from app.backend.services.event_handler_service import EventHandlerService
from app.backend.services.monitor_service import MonitorService
from app.backend.services.notification_service import NotificationService
from app.backend.services.restart_service import RestartService


class AgentRuntime:
    def __init__(self, config, logger, provider):
        self.config: Config = config
        self.logger: Logger = logger
        self.provider: ContainerProvider = provider

        self.loop = None
        self.stop_event = asyncio.Event()
    
    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._run())

    async def _run(self):
        restart_service = RestartService(restart_policy=self.config.restart_policy, client=self.provider, logger=self.logger)
        notification_service = NotificationService(logger=self.logger, config=self.config)
        handler = EventHandlerService(client=self.provider, config=self.config, restart_service=restart_service, notification_service=notification_service, logger=self.logger)

        monitor = MonitorService(
            client=self.provider,
            config=self.config,
            handler=handler,
            logger=self.logger
        )

        task = asyncio.create_task(monitor.monitor())

        await self.stop_event.wait()

        task.cancel()