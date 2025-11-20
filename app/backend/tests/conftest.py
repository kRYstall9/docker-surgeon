import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.backend.core import database
from app.backend.core.database import Base


@pytest.fixture(autouse=True)
def db_engine(monkeypatch):
    """Create an in-memory SQLite DB and patch SessionLocal for tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Create tables
    Base.metadata.create_all(engine)

    # Monkeypatch the SessionLocal used by repositories
    monkeypatch.setattr(database, 'engine', engine)
    monkeypatch.setattr(database, 'SessionLocal', TestingSessionLocal)

    # Also patch repository modules that imported SessionLocal at import time
    import importlib
    repo_names = [
        'app.backend.repositories.crashed_container_repository',
        'app.backend.repositories.user_repository'
    ]
    for name in repo_names:
        try:
            mod = importlib.import_module(name)
            monkeypatch.setattr(mod, 'SessionLocal', TestingSessionLocal)
        except Exception:
            # if module not imported yet, skip
            pass

    yield TestingSessionLocal

    # Teardown: drop tables and dispose engine to close all DB connections
    try:
        Base.metadata.drop_all(engine)
    except Exception:
        pass
    try:
        engine.dispose()
    except Exception:
        pass
    # force garbage collection to help close unreferenced DB handles
    import gc
    gc.collect()


@pytest.fixture
def logger():
    import logging
    return logging.getLogger('test_logger')
