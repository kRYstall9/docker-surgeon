from pydantic import BaseModel, Field
from datetime import date

class ChartStats(BaseModel):
    container_id:str = Field(description="The unique identifier of the container")
    container_name:str = Field(description="The name of the container")
    crash_count:int = Field(description="The number of times the container has crashed on the specified date")
    crashed_on:date
