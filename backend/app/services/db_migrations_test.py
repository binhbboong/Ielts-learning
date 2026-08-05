from alembic import command
from alembic.config import Config
from pathlib import Path

from app.core.config import settings
from app.services.db_migrations import upgrade_to_head

_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def _config_for_test_db() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)
    cfg.set_main_option("script_location", str(_ALEMBIC_INI.parent / "alembic"))
    return cfg


def test_upgrade_to_head_migrates_a_database_starting_from_empty(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", settings.TEST_DATABASE_URL)
    cfg = _config_for_test_db()
    command.downgrade(cfg, "base")
    try:
        revision = upgrade_to_head()
        assert revision == "0021"
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_to_head_is_a_no_op_when_already_at_head(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", settings.TEST_DATABASE_URL)
    cfg = _config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        revision = upgrade_to_head()
        assert revision == "0021"
    finally:
        command.downgrade(cfg, "base")
