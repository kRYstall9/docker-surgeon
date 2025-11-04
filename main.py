from app.DAL.database import init_db
from app.utils.config import Config
from app.utils.logger import get_bootstrap_logger, get_logger
from app.worker.monitor_service import monitor_containers
from threading import Thread

if __name__  == '__main__':
    
    logger = get_bootstrap_logger()
    
    try:
        config = Config.load()
    except Exception as e:
        logger.error(e)
    
    logger = get_logger(config)
    logger.info(f"Config successfully loaded!\n{config}")
    init_db(logger)
    
    Thread(target=monitor_containers, args=(config, logger)).start()
    