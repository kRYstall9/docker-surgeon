from app.backend.core.database import init_db
from app.backend.core.config import Config
from app.backend.core import state
from app.backend.core.logger import get_bootstrap_logger, get_logger
from app.backend.services.monitor_service import monitor_containers
from threading import Thread


if __name__  == '__main__':
    
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
    worker = Thread(target=monitor_containers, args=(config, logger), daemon=True)
    worker.start()
    
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
    
    worker.join()
    
    
    
