from logging import Logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import os

DB_URI = os.getenv('DATABASE_URI', 'sqlite:///./app/data/database.db')
INITIAL_MIGRATION_ID = '2a3ad493a301'

engine = create_engine(DB_URI, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(logger:Logger):
    from app.backend.models.crashed_container import CrashedContainer
    apply_migrations(logger)
    logger.info('DB initialized')

def apply_migrations(logger:Logger):
    logger.info(f"Executing {apply_migrations.__name__}")

    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', DB_URI)
    alembic_cfg.set_main_option('script_location', 'app/DBMigrations')

    with engine.connect() as conn:

        if not has_alembic_version(conn):
            logger.info("Legacy database detected, stamping initial version")
            command.stamp(alembic_cfg, INITIAL_MIGRATION_ID)
        
        logger.info('Applying pending migrations')
        command.upgrade(alembic_cfg, 'head')

def has_alembic_version(conn):
    try:
        conn.execute(text('SELECT 1 FROM alembic_version LIMIT 1'))
        return True
    except Exception:
        return False