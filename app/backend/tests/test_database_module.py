from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.backend.core import database


def test_init_db_creates_tables_and_logs(monkeypatch):
    # Create an in-memory engine and patch the module
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(database, 'engine', engine)
    monkeypatch.setattr(database, 'SessionLocal', TestingSessionLocal)

    class DummyLogger:
        def __init__(self):
            self.msg = None

        def info(self, m):
            self.msg = m

    logger = DummyLogger()

    # Call init_db which should create tables and call logger.info
    database.init_db(logger)

    inspector = inspect(engine)
    assert inspector.has_table('crashedcontainers')
    assert logger.msg and 'DB initialized' in logger.msg


def test_engine_and_sessionlocal_are_defined():
    # Ensure engine and SessionLocal exist and can produce a session
    assert hasattr(database, 'engine')
    assert hasattr(database, 'SessionLocal')

    sess = database.SessionLocal()
    try:
        assert hasattr(sess, 'commit')
    finally:
        sess.close()
