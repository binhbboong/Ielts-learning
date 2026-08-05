import os
from importlib import reload

import pytest

from app.core import config as config_module


@pytest.fixture(autouse=True)
def _restore_settings_singleton():
    """Every test below calls reload(config_module) to rebuild Settings()
    from monkeypatched env vars, which permanently replaces the module-level
    `settings` object other modules already hold a reference to (monkeypatch
    only undoes monkeypatch.setenv, not this). Without restoring it, later
    tests that make a real DB connection via settings.DATABASE_URL (e.g.
    app/services/db_migrations_test.py) inherit this file's dummy
    'postgresql://u:p@localhost:5433/db' value instead of the real one."""
    original = config_module.settings
    try:
        yield
    finally:
        config_module.settings = original


def test_settings_has_session_and_password_fields(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("LEARNER_PASSWORD_HASH", "test-hash")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5433/db")
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql://u:p@localhost:5433/testdb")

    from app.core import config as config_module

    reload(config_module)
    settings = config_module.Settings()

    assert settings.SESSION_SECRET == "test-secret"
    assert settings.LEARNER_PASSWORD_HASH == "test-hash"
    assert settings.DATABASE_URL == "postgresql://u:p@localhost:5433/db"
    assert settings.TEST_DATABASE_URL == "postgresql://u:p@localhost:5433/testdb"


def test_session_cookie_max_age_days_defaults_to_30(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("LEARNER_PASSWORD_HASH", "test-hash")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5433/db")
    monkeypatch.delenv("SESSION_COOKIE_MAX_AGE_DAYS", raising=False)

    from app.core import config as config_module

    reload(config_module)
    settings = config_module.Settings()

    assert settings.SESSION_COOKIE_MAX_AGE_DAYS == 30


def test_session_cookie_max_age_days_reads_from_env(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("LEARNER_PASSWORD_HASH", "test-hash")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5433/db")
    monkeypatch.setenv("SESSION_COOKIE_MAX_AGE_DAYS", "7")

    from app.core import config as config_module

    reload(config_module)
    settings = config_module.Settings()

    assert settings.SESSION_COOKIE_MAX_AGE_DAYS == 7


def test_learner_timezone_defaults_to_ho_chi_minh(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("LEARNER_PASSWORD_HASH", "test-hash")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5433/db")
    monkeypatch.delenv("LEARNER_TIMEZONE", raising=False)

    from app.core import config as config_module

    reload(config_module)
    settings = config_module.Settings()

    assert settings.LEARNER_TIMEZONE == "Asia/Ho_Chi_Minh"
