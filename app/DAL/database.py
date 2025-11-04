from logging import Logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///./data/database.db', echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


def init_db(logger:Logger):
    from app.DAL.models import CrashedContainer, Container
    Base.metadata.create_all(engine)
    
    logger.info('DB initialized')