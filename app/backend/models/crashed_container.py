from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class CrashedContainer(Base):
    __tablename__ = 'crashedcontainers'
    
    id = Column(Integer, primary_key=True)
    containerid = Column(String(100), ForeignKey('containers.containerid'))
    logs = Column(String(5000), nullable=True)
    crashedon = Column(DateTime, nullable=False)
    
    container = relationship('Container', back_populates='crashedcontainers')
    
    def __repr__(self):
        return f"<CrashedContainer(name= '{self.container.containername}', containerId='{self.containerid}')>"

