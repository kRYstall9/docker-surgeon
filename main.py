from app.backend.core import Config
from app.backend.core import get_bootstrap_logger, get_logger
from app.backend.core.database import init_db
from app.backend.core.runtime import Runtime
from threading import Thread
from app.backend.providers import DockerClientProvider
import docker


def bootstrap():
    logger = get_bootstrap_logger()

    config = Config.load()
    logger = get_logger(config)

    init_db(logger)

    return config, logger

def run_runtime(runtime: Runtime):
    runtime.start()

def run_agent():
    config, logger = bootstrap()

    from app.agent import AgentServer
    logger.info(f"Starting agent server at {config.agent_host}:{config.agent_port}")
    if config.agent_host is None or config.agent_port is None:
        logger.error("Agent host or port is not configured. Please set AGENT_HOST and AGENT_PORT in the environment variables.")
        exit(1)
    
    agent_server = AgentServer(config, logger)
    agent_server.run()

def run_server():
    config, logger = bootstrap()

    threads: list[Thread] = []
    runtimes = []

    # =========================
    # 1. LOCAL DOCKER RUNTIME
    # =========================
    logger.info("Starting LOCAL docker runtime")

    local_docker = docker.from_env()
    local_provider = DockerClientProvider(local_docker)

    local_runtime = Runtime(config, logger, local_provider)

    t = Thread(
        target=run_runtime,
        args=(local_runtime,),
        daemon=True
    )
    t.start()
    threads.append(t)

    # =========================
    # 2. AGENT/S RUNTIME
    # =========================
    for agent in config.agents_config:
        logger.info(f"Starting agent {agent.name}")

        if not agent.host or not agent.port or not agent.token:
            logger.error(f"Invalid config for agent {agent.name}")
            continue
        
        from app.agent.utils.agent_logger import AgentLogger
        from app.agent import AgentClient
        from app.backend.providers import AgentClientProvider

        agent_logger = AgentLogger(logger, extra={"agent_name": agent.name})

        agent_client = AgentClient(
            base_url=agent.base_url,
            token=agent.token,
            logger=logger,
            name=agent.name
        )

        provider = AgentClientProvider(agent_client)

        runtime = Runtime(config, agent_logger, provider)
        runtimes.append(runtime)

        t = Thread(
            target=run_runtime,
            args=(runtime,),
            daemon=True
        )

        t.start()
        threads.append(t)

    if config.enable_dashboard:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        from app.backend.api.api_router import api_router
        from fastapi.responses import FileResponse
        from os import path

        logger.info("Starting FastAPI server for Docker Surgeon API...")
        DASHBOARD_DIR = "app/dashboard_build"

        app = FastAPI(
            title="Docker Surgeon API",
            description="A tool to monitor and manage Docker containers."
        )  

        app.mount(
            "/assets",
            StaticFiles(directory=f"{DASHBOARD_DIR}/assets"),
            name="assets"
        )
        app.include_router(api_router, prefix="/api")

        @app.get("/{full_path:path}")
        def serve_dashboard(full_path: str):
            return FileResponse(path.join(DASHBOARD_DIR, "index.html"))
        
        uvicorn.run(app, host= config.dashboard_address, port= config.dashboard_port, reload=False)
        logger.info("FastAPI server started")

    for t in threads:
        t.join()