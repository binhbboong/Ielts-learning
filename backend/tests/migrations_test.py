from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import settings

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _alembic_config_for_test_db() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    return cfg


def test_upgrade_head_creates_login_attempt_table_then_downgrade_removes_it():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        assert "login_attempt" in inspector.get_table_names()
        columns = {c["name"] for c in inspector.get_columns("login_attempt")}
        assert columns == {"id", "ip_address", "occurred_at", "succeeded"}
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_head_creates_listening_practice_tables_then_downgrade_to_0008_removes_them():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "listening_exercises" in table_names
        assert "listening_questions" in table_names
        assert "listening_submissions" in table_names

        exercise_columns = {
            c["name"] for c in inspector.get_columns("listening_exercises")
        }
        assert exercise_columns == {
            "id",
            "day",
            "script_text",
            "audio_bytes",
            "audio_content_type",
            "focus_reference",
            "status",
            "created_at",
        }
        engine.dispose()

        command.downgrade(cfg, "0008")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "listening_exercises" not in table_names
        assert "listening_questions" not in table_names
        assert "listening_submissions" not in table_names
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_head_creates_daily_focus_table_then_downgrade_to_0009_removes_it():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        assert "daily_focus" in inspector.get_table_names()
        columns = {c["name"] for c in inspector.get_columns("daily_focus")}
        assert columns == {
            "id",
            "day",
            "skill",
            "focus_kind",
            "focus_reference",
            "created_at",
        }
        engine.dispose()

        command.downgrade(cfg, "0009")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        assert "daily_focus" not in inspector.get_table_names()
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_head_creates_reading_practice_tables_then_downgrade_to_0007_removes_them():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "reading_exercises" in table_names
        assert "reading_questions" in table_names
        assert "reading_submissions" in table_names

        exercise_columns = {c["name"] for c in inspector.get_columns("reading_exercises")}
        assert exercise_columns == {
            "id",
            "day",
            "passage_text",
            "focus_reference",
            "status",
            "created_at",
        }
        engine.dispose()

        command.downgrade(cfg, "0007")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "reading_exercises" not in table_names
        assert "reading_questions" not in table_names
        assert "reading_submissions" not in table_names
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")
