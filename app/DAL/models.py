from sqlalchemy import Column, Integer, String, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from app.DAL.database import Base

class Container(Base):
    __tablename__ = "containers"
    
    id = Column(Integer, primary_key=True)
    containername = Column(String(200), unique=True, nullable=False)
    containerid = Column(String(100), unique=True, nullable=False)
    
    crashedcontainers = relationship('CrashedContainer', back_populates='container')
    
    def __repr__(self):
        return f"<Container(name='{self.containername}', containerid='{self.containerid}')>"

class CrashedContainer(Base):
    __tablename__ = 'crashedcontainers'
    
    id = Column(Integer, primary_key=True)
    containerid = Column(String(100), ForeignKey('containers.containerid'))
    logs = Column(String(5000), nullable=True)
    crashedon = Column(Date, nullable=False)
    
    container = relationship('Container', back_populates='crashedcontainers')
    
    def __repr__(self):
        return f"<CrashedContainer(name= '{self.container.containername}', containerId='{self.containerid}')>"


    

