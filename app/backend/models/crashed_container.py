from sqlalchemy import Column, Integer, String, DateTime
from app.backend.core.database import Base


class CrashedContainer(Base):
    __tablename__ = 'crashedcontainers'
    
    id = Column(Integer, primary_key=True)
    container_id = Column(String(100))
    container_name = Column(String(100))
    logs = Column(String(5000), nullable=True)
    crashedon = Column(DateTime, nullable=False)
 
    def __repr__(self):
        return f"<CrashedContainer(name= '{self.container_name}', containerId='{self.container_id}')>"

