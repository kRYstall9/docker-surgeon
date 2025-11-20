from logging import Logger
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///./app/data/database.db', echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(logger:Logger):
    from app.backend.models.crashed_container import CrashedContainer
    
    Base.metadata.create_all(engine)
    
    logger.info('DB initialized')