from app.backend.core.config import Config
import pytest

def test_config_load(monkeypatch):
    monkeypatch.setenv("RESTART_POLICY", '{"excludedContainers":["a"], "statuses": {}}')
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_TIMEZONE", "UTC")
    monkeypatch.setenv("ENABLE_DASHBOARD", "True")
    monkeypatch.setenv("LOGS_AMOUNT", "5")
    monkeypatch.setenv("DASHBOARD_ADDRESS", "127.0.0.1")
    monkeypatch.setenv("DASHBOARD_PORT", "9000")
    monkeypatch.setenv("ADMIN_PASSWORD", "adm")
    monkeypatch.setenv("ENABLE_NOTIFICATIONS", "True")
    monkeypatch.setenv("NOTIFICATION_URLS", '["http://example"]')
    monkeypatch.setenv("NOTIFICATION_TITLE", "T")
    monkeypatch.setenv("NOTIFICATION_BODY", "Line\\nNew")

    cfg = Config.load()
    assert cfg.log_level == "DEBUG"
    assert cfg.enable_dashboard is True
    assert cfg.logs_amount == 5
    assert cfg.dashboard_address == "127.0.0.1"
    assert cfg.dashboard_port == 9000
    assert cfg.enable_notifications is True
    assert cfg.notification_urls == ["http://example"]
    assert "Line\nNew" in (cfg.notification_body or "")


def test_config_notification_urls_malformed(monkeypatch):
    # NOTIFICATION_URLS invalid JSON should fallback to []
    monkeypatch.setenv("RESTART_POLICY", '{}')
    monkeypatch.setenv("NOTIFICATION_URLS", 'not-a-json')
    cfg = Config.load()
    assert cfg.notification_urls == []


def test_config_load_raises(monkeypatch):
    # invalid restart_policy JSON should raise an Exception from load()
    monkeypatch.setenv("RESTART_POLICY", '{bad')
    with pytest.raises(Exception):
        Config.load()


def test_config_get_raises(monkeypatch):
    # If load() raises, get() should re-raise an Exception
    def fake_load():
        raise Exception("boom")

    monkeypatch.setattr(Config, 'load', staticmethod(fake_load))
    with pytest.raises(Exception):
        Config.get()


def test_config_get_returns_existing_instance(monkeypatch):
    # if _instance is already set, get() should return it without calling load
    sentinel = object()
    monkeypatch.setattr(Config, '_instance', sentinel)
    assert Config.get() is sentinel


def test_config_repr():
    cfg = Config({}, 'INFO', 'UTC', False, 1, 'addr', 1, None, False, [], None, None)
    r = repr(cfg)
    assert 'Restart Policy' in r and 'Log Level' in r