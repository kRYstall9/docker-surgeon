from datetime import datetime
from pydantic import BaseModel, Field


class CrashedContainerBase(BaseModel):
    container_id:str
    container_name:str
    
class CrashedContainerLogs(CrashedContainerBase):
    logs:str
    crashed_on:datetime
    
class CrashedContainerStats(CrashedContainerBase):
    crash_count:int
