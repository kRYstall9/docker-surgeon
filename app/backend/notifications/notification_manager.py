from app.backend.notifications.apprise_client import AppriseClient
from app.backend.core.logger import get_logger
from app.backend.core.config import Config
import re

config = Config.get()
logger = get_logger(config)
urls = [u.strip() for u in config.notification_urls]
client = AppriseClient(urls)
ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

class NotificationManager:
    @staticmethod
    def container_crashed_event(container_name:str, container_logs:str, container_exit_code:str):
        
        logger.info("Sending notifications")
        
        try:
            context = {
                "container_name": container_name,
                "logs": ANSI_ESCAPE.sub('',container_logs.decode('utf-8', errors='ignore')),
                "exit_code": container_exit_code,
                "n_logs": config.logs_amount
            }
            
            title = (config.notification_title or '⚠️ {container_name} crashed').format(**context)
            body = (config.notification_body or '`exit code`: `{exit_code}`\nLast {n_logs} logs of `{container_name}`: {logs}').format(**context)
            client.send(body=body, title=title)
        
            logger.info("Notification sent")
              
        except Exception as e:
            logger.error(e)