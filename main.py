import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.backend.core.config import Config
from app.backend.core.logger import get_bootstrap_logger, get_logger
from app.backend.core.database import init_db
from app.backend.notifications.apprise_client import AppriseClient
from app.backend.services.monitor_service import MonitorService
from app.backend.services.event_handler_service import EventHandlerService
from app.backend.services.restart_service import RestartService
from app.backend.services.notification_service import NotificationService
from app.backend.providers.container_provider import ContainerProvider
from app.agent.agent_runtime import AgentRuntime
from threading import Thread


def bootstrap():
    logger = get_bootstrap_logger()

    config = Config.load()
    logger = get_logger(config)

    init_db(logger)

    return config, logger

def run_runtime(runtime: AgentRuntime):
    runtime.start()


def run_server():
    config, logger = bootstrap()

    threads = []
    runtimes = []
    for agent in config.agents_config:
        logger.info(f"Starting agent {agent.name}")

        if not agent.host or not agent.port or not agent.token:
            logger.error(f"Invalid config for agent {agent.name}")
            continue
        
        from app.agent.utils.agent_logger import AgentLogger
        from app.agent.agent_client import AgentClient
        from app.backend.providers.agent_client_provider import AgentClientProvider

        agent_logger = AgentLogger(logger, extra={"agent_name": agent.name})

        agent_client = AgentClient(
            base_url=agent.base_url,
            token=agent.token,
            logger=logger
        )

        provider = AgentClientProvider(agent_client)

        runtime = AgentRuntime(config, agent_logger, provider)
        runtimes.append(runtime)

        t = Thread(
            target=run_runtime,
            args=(runtime,),
            daemon=True
        )

        t.start()
        threads.append(t)

    if config.enable_dashboard:
        app = FastAPI()

        from app.backend.api.api_router import api_router
        app.include_router(api_router, prefix="/api")

        uvicorn.run(
            app,
            host=config.dashboard_address,
            port=config.dashboard_port
        )
        
    for t in threads:
        t.join()