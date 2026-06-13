from logging import Logger
from app.backend.core.config import Config
from app.backend.events.event import Event
from app.backend.providers.container_provider import ContainerProvider
from app.backend.services.notification_service import NotificationService
from app.backend.services.restart_service import RestartService
from time import time

class EventHandlerService:
    # Seconds to wait after a container is restarted
    DELAY = 30

    def __init__(
            self,
            client: ContainerProvider,
            config: Config,
            restart_service: RestartService,
            notification_service: NotificationService,
            logger: Logger
        ):
        self.client = client
        self.config = config
        self.restart_service = restart_service
        self.notification_service = notification_service
        self.logger = logger
        self.cooldown = {}

    async def handle(self, event: Event):
        try:
            container = await self.client.get_container(event.container_id or event.container_name)
            if container is None:
                return
            
            last_event_time = self.cooldown.get(container.id or container.name)

            if last_event_time and time() - last_event_time < self.DELAY:
                return
            
            if await self.restart_service.can_be_restarted(container):
                logs = await self.client.get_logs(container.id or container.name, self.config.logs_amount)
                await self.restart_service.restart_with_graph(container)

                await self.notification_service.notify(container.name, logs, container.exit_code or '')

                self.cooldown[container.id or container.name] = time()
        except Exception as e:
            self.logger.error(e)


