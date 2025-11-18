import json
from threading import Lock
from dotenv import load_dotenv
from os import getenv
from app.backend.utils.string_utils import normalize_escapes

class Config:
    _instance = None
    _lock = Lock()
    restart_policy:any
    log_level:str
    timezone:str
    enable_dashboard:bool
    logs_amount:int
    dashboard_address:str
    dashboard_port:int
    admin_password:str | None
    enable_notifications:bool
    notification_urls:list[str]
    notification_title:str | None
    notification_body:str | None
    
    def __init__(self, restart_policy:any, log_level:str, timezone:str, enable_dashboard:bool, logs_amount:int, dashboard_address:str, dashboard_port:int, admin_password: str | None, enable_notifications:bool, notification_urls:list[str], notification_title:str | None, notification_body:str | None):
        self.restart_policy = restart_policy
        self.log_level = log_level
        self.timezone = timezone
        self.enable_dashboard = enable_dashboard
        self.logs_amount = logs_amount
        self.dashboard_address = dashboard_address
        self.dashboard_port = dashboard_port
        self.admin_password = admin_password
        self.enable_notifications = enable_notifications
        self.notification_urls = notification_urls
        self.notification_title = notification_title
        self.notification_body = notification_body
    
    @classmethod
    def load(cls):
        try:
            load_dotenv()
            restart_policy = getenv("RESTART_POLICY")
            notification_urls = getenv("NOTIFICATION_URLS", [])
            
            return cls(
                restart_policy = json.loads(restart_policy),
                log_level = getenv("LOG_LEVEL", "INFO").upper(),
                timezone = getenv("LOG_TIMEZONE", "UTC"),
                enable_dashboard = getenv("ENABLE_DASHBOARD", False).lower() == "true",
                logs_amount = getenv("LOGS_AMOUNT", 10),
                dashboard_address = getenv("DASHBOARD_ADDRESS", "0.0.0.0"),
                dashboard_port = int(getenv("DASHBOARD_PORT", 8000)),
                admin_password = getenv("ADMIN_PASSWORD", None),
                enable_notifications = getenv("ENABLE_NOTIFICATIONS", False).lower() == "true",
                notification_urls= json.loads(notification_urls),
                notification_title = getenv("NOTIFICATION_TITLE", None),
                notification_body = normalize_escapes(getenv("NOTIFICATION_BODY", None))
            )
        except Exception as e:
            raise Exception(f"Unable to load the config: {e}")
    
    @classmethod
    def get(cls):
        try:
            if cls._instance is None:
                with cls._lock:
                    if cls._instance is None:
                        cls._instance = cls.load()
            
            return cls._instance
        except Exception as e:
            raise Exception(e)
        

    def __repr__(self):
        return f"Config:\nRestart Policy: {self.restart_policy}\nLog Level: {self.log_level}\nTime Zone: {self.timezone}\nEnable Dashboard: {self.enable_dashboard}\nDashboard Address: {self.dashboard_address}\nDashboard Port: {self.dashboard_port}\nLogs Amount: {self.logs_amount}\nEnable Notifications: {self.enable_notifications}"
        