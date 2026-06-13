from __future__ import annotations
from logging import Logger
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.backend.core import Config
    from app.backend.notifications import AppriseClient


class NotificationService:
    ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.client = AppriseClient(self.config.notification_urls)
    
    async def notify(self, container_name:str, container_logs:str, container_exit_code:str):
        
        self.logger.info("Sending notifications")
        
        try:
            context = {
                "container_name": container_name,
                "logs": self.ANSI_ESCAPE.sub('',container_logs),
                "exit_code": container_exit_code,
                "n_logs": self.config.logs_amount
            }
            
            title = (self.config.notification_title or '⚠️ {container_name} crashed').format(**context)
            body = (self.config.notification_body or '`exit code`: `{exit_code}`\nLast {n_logs} logs of `{container_name}`: {logs}').format(**context)
            self.client.send(body=body, title=title)
        
            self.logger.info("Notification sent")
              
        except Exception as e:
            self.logger.error(f"An error occured while sending a notification. Error: {e}")