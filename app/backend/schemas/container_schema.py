from pydantic import BaseModel

class ContainerBase(BaseModel):
    name: str
    cid: str