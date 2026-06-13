from app.backend.core.config import Config
import pytz
from datetime import datetime
import logging
from logging import Logger

class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        prefix = []

        if self.extra.get("agent_name"):
            prefix.append(f"Agent={self.extra['agent_name']}")

        if self.extra.get("container_name"):
            prefix.append(f"Container={self.extra['container_name']}")

        if self.extra.get("event"):
            prefix.append(f"Event={self.extra['event']}")

        if prefix:
            msg = f"[{' | '.join(prefix)}] {msg}"

        return msg, kwargs


def get_logger(config:Config, name:str = __name__) -> Logger:
    
    try:
        tz = pytz.timezone(config.timezone)
    except Exception:
        tz = pytz.UTC
        logging.warning(f"Timezone '{config.timezone}' not valid. Using UTC")
        
    def time_in_tz(*args):
        return datetime.now(tz).timetuple()
    
    logger = logging.getLogger(name)
    logger.setLevel(config.log_level)
    logger.propagate = False
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - Func: %(funcName)s - [MSG]: %(message)s')
        formatter.converter = time_in_tz
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_bootstrap_logger() -> Logger:
    
    logger = logging.getLogger("bootstrap")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - Func: %(funcName)s - [MSG]: %(message)s'))
        logger.addHandler(handler)
        
    return logger

def get_context_logger(base_logger: Logger, **context):
    return ContextLogger(base_logger, context)
    
    