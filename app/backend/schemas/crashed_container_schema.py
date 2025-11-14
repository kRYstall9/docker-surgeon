from datetime import datetime
from pydantic import BaseModel, Field


class CrashedContainerBase(BaseModel):
    container_id:str
    container_name: str | None = None
    logs:str
    
class CrashedContainerLogs(CrashedContainerBase):
    crashed_on:datetime
    
class CrashedContainerStats(CrashedContainerBase):
    crash_count:int
