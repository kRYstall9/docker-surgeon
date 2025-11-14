from pydantic import BaseModel, ConfigDict, Field

class ContainerBase(BaseModel):
    name: str = Field(alias='containername')
    cid: str = Field(alias='containerid')

class ContainerCreate(ContainerBase):
    pass

class Container(ContainerBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)