from __future__ import annotations
from logging import Logger
from time import time
from typing import TYPE_CHECKING
from app.agent import AgentClient
from app.backend.repositories.crashed_container_repository import CrashedContainerRepository
from app.backend.schemas.crashed_container_schema import CrashedContainerBase
from app.backend.schemas.container_history import ContainerHistory
from app.backend.providers import AgentClientProvider

if TYPE_CHECKING:
    from app.backend.core import Config
    from app.backend.events import Event
    from app.backend.providers import ContainerProvider
    from app.backend.services import NotificationService, RestartService
    from app.backend.models import ContainerProxy


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
        self.history: list[ContainerHistory] = []

    async def handle(self, event: Event):
        try:
            self.logger.debug(f"Handling event {event.type} for container {event.container_name}")

            container = await self.client.get_container(event.container_id or event.container_name)
            if container is None:
                return

            last_event_time = self.cooldown.get(container.id or container.name)

            if last_event_time and time() - last_event_time < self.DELAY:
                return

            self.manage_history(container)

            if await self.restart_service.can_be_restarted(container):
                logs = await self.client.get_logs(container.id or container.name, self.config.logs_amount)
                await self.restart_service.restart_with_graph(container)

                agent_name: str | None = self.client.client.name if type(self.client.client) is AgentClient else None
                await self.notification_service.notify(container.name, logs, container.exit_code or '', agent_name)

                # If the agent name is not available, the event happened on the server, so we set the machine to 'Server'. Otherwise, we set it to the agent name.
                machine = agent_name if agent_name else 'Server'

                ## Add record to the CrashedContainer table
                crashed_container = CrashedContainerBase(container_id=container.id, container_name=container.name, logs=logs, machine=machine)
                CrashedContainerRepository.add_crashed_container(crashed_container, self.logger)

                self.cooldown[container.id or container.name] = time()
        except Exception as e:
            self.logger.error(e)

    def manage_history(self, container: ContainerProxy | None):
        if container is None:
            self.logger.debug('Container is None. Unable to check the container history')
            return

        host_name: str = 'server'

        if isinstance(self.client, AgentClientProvider):
            host_name = self.client.client.name.lower().strip()

        container_history = next((ct for ct in self.history if ct.container_name == container.name and ct.host_name == host_name), None)
        if container_history is not None:
            history_current_id = container_history.container_current_id
            current_id = container.id

            if history_current_id.lower().strip() != current_id.lower().strip():
                container_history.container_previous_id = container_history.container_current_id
                container_history.container_current_id = container.id
        else:
            container_history = ContainerHistory(host_name=host_name, container_name=container.name, container_current_id=container.id)
            self.history.append(container_history)
