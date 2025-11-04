import json
from dotenv import load_dotenv
from os import getenv

class Config:
    restart_policy:any
    log_level:str
    timezone:str
    enable_dashboard:bool
    logs_amount:int
    
    def __init__(self, restart_policy:any, log_level:str, timezone:str, enable_dashboard:bool, logs_amount:int):
        self.restart_policy = restart_policy
        self.log_level = log_level
        self.timezone = timezone
        self.enable_dashboard = enable_dashboard
        self.logs_amount = logs_amount
    
    @classmethod
    def load(cls):
        try:
            load_dotenv()
            restart_policy = getenv("RESTART_POLICY")
            
            return cls(
                restart_policy = json.loads(restart_policy),
                log_level = getenv("LOG_LEVEL", "INFO").upper(),
                timezone = getenv("LOG_TIMEZONE", "UTC"),
                enable_dashboard = getenv("ENABLE_DASHBOARD", True),
                logs_amount = getenv("LOGS_AMOUNT", 10)
            )
        except Exception as e:
            raise Exception(f"Unable to load the config: {e}")
        

    def __repr__(self):
        return f"Config:\nRestart Policy: {self.restart_policy}\nLog Level: {self.log_level}\nTime Zone: {self.timezone}\nEnable Dashboard: {self.enable_dashboard}\nLogs Amount: {self.logs_amount}"
        