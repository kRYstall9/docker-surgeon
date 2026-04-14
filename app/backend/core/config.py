from dataclasses import field, dataclass
import json
from threading import Lock
from typing import Any, ClassVar
from dotenv import load_dotenv
from os import getenv
from app.backend.core.agent_config import AgentConfig
from app.backend.utils.string_utils import normalize_escapes

@dataclass
class Config:
    _instance: ClassVar["Config | None"] = None
    _lock: ClassVar[Lock] = Lock()
    
    restart_policy: Any
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
    agents_config: list[AgentConfig] = field(default_factory=list)
    agent_host: str | None = None
    agent_port: int | None = None
    agent_token: str | None = None
    
    @classmethod
    def load(cls):
        try:
            load_dotenv()
            restart_policy = getenv("RESTART_POLICY", "")
            notification_urls = getenv("NOTIFICATION_URLS", "")
            
            try:
                notification_urls = json.loads(notification_urls) if notification_urls else []
            except:
                notification_urls = []
            
            return cls(
                restart_policy = json.loads(restart_policy) if len(restart_policy) > 0 else {},
                log_level = getenv("LOG_LEVEL", "INFO").upper(),
                timezone = getenv("LOG_TIMEZONE", "UTC"),
                enable_dashboard = getenv("ENABLE_DASHBOARD", "false").strip().lower() == "true",
                logs_amount = int(getenv("LOGS_AMOUNT", "10")),
                dashboard_address = getenv("DASHBOARD_ADDRESS", "0.0.0.0"),
                dashboard_port = int(getenv("DASHBOARD_PORT", "8000")),
                admin_password = getenv("ADMIN_PASSWORD", None),
                enable_notifications = getenv("ENABLE_NOTIFICATIONS", "false").strip().lower() == "true",
                notification_urls= notification_urls,
                notification_title = getenv("NOTIFICATION_TITLE", None),
                notification_body = normalize_escapes(getenv("NOTIFICATION_BODY", None)),
                agents_config = [AgentConfig.from_dict(agent) for agent in json.loads(getenv("AGENTS_CONFIG", "[]"))],
                agent_host = getenv("AGENT_HOST", "127.0.0.1"),
                agent_port = int(getenv("AGENT_PORT", "8000")),
                agent_token = getenv("AGENT_TOKEN", None)
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