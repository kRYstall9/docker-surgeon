from app.backend.core.agent_config import AgentConfig
from app.backend.core.database import init_db
from app.backend.core.config import Config
from app.backend.core import state
from app.backend.core.logger import get_bootstrap_logger, get_logger
from app.backend.services.monitor_service import monitor_containers
from app.agent.utils.agent_logger import AgentLogger
from threading import Thread
import uvicorn


def bootstrap():
    logger = get_bootstrap_logger()
    
    try:
        config = Config.load()
        state.config = config
    except Exception as e:
        logger.error(e)
        exit(1)
    
    logger = get_logger(config)
    logger.info(f"Config successfully loaded!\n{config}")
    state.logger = logger
    init_db(logger)
    
    return config, logger

def run_agent():
    config, logger = bootstrap()
    
    state.logger = logger
    state.config = config
    
    from app.agent.agent_server import app as agent_app
    logger.info(f"Starting agent server at {config.agent_host}:{config.agent_port}")
    uvicorn.run(agent_app, host=config.agent_host, port=config.agent_port)

def run_server():
    config, logger = bootstrap()
    workers = []
    
    worker = Thread(target=monitor_containers, args=(config, logger), daemon=True)
    worker.start()
    workers.append(worker)
                
    for agent in config.agents_config:
        logger.info(f"Starting agent client for {agent.name} at {agent.host}:{agent.port}")
        from app.agent.agent_client import AgentClient
        logger = AgentLogger(logger, extra={"agent_name": agent.name})
        agent_client = AgentClient(base_url=agent.base_url, token=agent.token, logger=logger)
        
        worker = Thread(target=monitor_containers, args=(config, logger, True, agent_client), daemon=True)
        worker.start()
        workers.append(worker)
    
    if config.enable_dashboard:
        import uvicorn
        from os import path
        from fastapi import FastAPI
        from app.backend.api.api_router import api_router
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
        
        logger.info("Starting FastAPI server for Docker Surgeon API...")
        DASHBOARD_DIR = "app/dashboard_build"
        
        app = FastAPI(
            title="Docker Surgeon API",
            description="A tool to monitor and manage Docker containers."
        )    
            
        app.mount('/assets', StaticFiles(directory=f"{DASHBOARD_DIR}/assets"), name="assets")   
        app.include_router(router=api_router, prefix='/api')
        
        @app.get("/{full_path:path}")
        def serve_dashboard(full_path:str):
            index_path = path.join(f"{DASHBOARD_DIR}", "index.html")
            return FileResponse(index_path)
            
        uvicorn.run(app, host=config.dashboard_address, port=config.dashboard_port, reload=False)
        logger.info("FastAPI server started")

    for worker in workers:
        worker.join()
    
