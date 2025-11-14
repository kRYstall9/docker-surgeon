from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.backend.core.database import Base

class Container(Base):
    __tablename__ = "containers"
    
    id = Column(Integer, primary_key=True)
    containername = Column(String(200), unique=True, nullable=False)
    containerid = Column(String(100), unique=True, nullable=False)
    
    crashedcontainers = relationship('CrashedContainer', back_populates='container')
    
    def __repr__(self):
        return f"<Container(name='{self.containername}', containerid='{self.containerid}')>"