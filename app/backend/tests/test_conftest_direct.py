
import pytest
from app.backend.tests import conftest as confmod


def _call_db_engine_with_monkeypatch(monkeypatch_obj):
    # call the original function wrapped by pytest.fixture via __wrapped__
    gen = confmod.db_engine.__wrapped__(monkeypatch_obj)
    # run setup part until yield
    sessmaker = next(gen)
    # basic assertion: sessmaker is callable
    assert callable(sessmaker)
    # create and close a session to exercise returned sessionmaker
    s = sessmaker()
    s.close()
    # run teardown
    try:
        gen.close()
    finally:
        # undo monkeypatch changes
        try:
            monkeypatch_obj.undo()
        except Exception:
            pass


def test_db_engine_generator_success():
    mp = pytest.MonkeyPatch()
    _call_db_engine_with_monkeypatch(mp)


def test_db_engine_importlib_failure_branch():
    mp = pytest.MonkeyPatch()

    # make importlib.import_module raise for at least one repo name to hit except branch
    import importlib as _importlib

    real_import = _importlib.import_module

    def fake_import(name):
        # raise for the repository modules to simulate ImportError
        if 'app.backend.repositories' in name:
            raise ImportError('simulated')
        return real_import(name)

    mp.setattr(_importlib, 'import_module', fake_import)

    _call_db_engine_with_monkeypatch(mp)
