from typing import Optional
from pydantic import BaseModel, Field

class ContainerHistory(BaseModel):
    host_name: str = Field(description='The name of the host that is watching the container')
    container_name: str = Field(description='The name of the container')
    container_current_id: str = Field(description='The current id of the container')
    container_previous_id: Optional[str] = Field(default= None, description='The previous id of the container')
    

