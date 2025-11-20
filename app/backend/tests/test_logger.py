import logging
from types import SimpleNamespace
from app.backend.core.logger import get_logger, get_bootstrap_logger
import logging

def test_get_logger_fallback_timezone(caplog):
    caplog.set_level(logging.WARNING)
    cfg = SimpleNamespace(timezone="Invalid/Zone", log_level="INFO")
    logger = get_logger(cfg, name="test_logger")
    assert logger.level == logging.INFO
    # get_logger logs a warning like "Using UTC" when timezone is invalid
    assert any("Using UTC" in rec.message for rec in caplog.records)

def test_get_bootstrap_logger():
    logger = get_bootstrap_logger()
    assert logger.name == "bootstrap"
    assert logger.level == logging.INFO


def test_time_in_tz_converter():
    # Ensure the formatter.converter (time_in_tz) is callable and returns a timetuple
    cfg = SimpleNamespace(timezone="UTC", log_level="INFO")
    logger = get_logger(cfg, name="test_logger_converter")
    # find formatter from handler
    assert logger.handlers, "logger should have handlers"
    fmt = logger.handlers[0].formatter
    # converter should be a callable that returns a timetuple
    tup = fmt.converter()
    assert isinstance(tup, tuple)