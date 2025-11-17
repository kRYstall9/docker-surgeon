from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.backend.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(200), unique=True, nullable=False)
    password = Column(String(100), unique=True, nullable=False)
    createdon = Column(Date, nullable=False)
     
    def __repr__(self):
        return f"<User(name='{self.username}')>"