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
        # script_text/audio_bytes/audio_content_type moved to listening_sections
        # (migration 0020 — see docs/adr/2026-08-05-ielts-exam-structure-band-
        # scaling.md).
        assert exercise_columns == {
            "id",
            "user_id",
            "day",
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


def test_upgrade_head_adds_generated_prompt_text_then_downgrade_to_0012_removes_it():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("daily_focus")}
        assert "generated_prompt_text" in columns
        engine.dispose()

        command.downgrade(cfg, "0012")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("daily_focus")}
        assert "generated_prompt_text" not in columns
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_head_adds_daily_prompt_columns_then_downgrade_to_0011_removes_them():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)

        writing_columns = {c["name"] for c in inspector.get_columns("writing_submissions")}
        assert "day" in writing_columns

        speaking_columns = {
            c["name"]: c for c in inspector.get_columns("speaking_submissions")
        }
        assert "day" in speaking_columns
        assert "prompt_text" in speaking_columns
        assert speaking_columns["question_id"]["nullable"] is True
        engine.dispose()

        command.downgrade(cfg, "0011")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        writing_columns = {c["name"] for c in inspector.get_columns("writing_submissions")}
        assert "day" not in writing_columns
        speaking_columns = {
            c["name"]: c for c in inspector.get_columns("speaking_submissions")
        }
        assert "day" not in speaking_columns
        assert "prompt_text" not in speaking_columns
        assert speaking_columns["question_id"]["nullable"] is False
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_head_drops_superseded_study_plan_tables_then_downgrade_to_0010_restores_them():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "tasks" not in table_names
        assert "plan_state" not in table_names
        engine.dispose()

        command.downgrade(cfg, "0010")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "tasks" in table_names
        assert "plan_state" in table_names
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
        # task_type added by migration 0021 (Writing Task 1/Task 2 alternation —
        # see docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md).
        assert columns == {
            "id",
            "user_id",
            "day",
            "skill",
            "focus_kind",
            "focus_reference",
            "generated_prompt_text",
            "task_type",
            "target_band",
            "estimated_minutes",
            "priority",
            "phase",
            "rationale",
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


def test_upgrade_head_adds_review_session_day_then_downgrade_to_0016_removes_it():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("review_sessions")}
        assert "day" in columns
        index_names = {idx["name"] for idx in inspector.get_indexes("review_sessions")}
        assert "ix_review_sessions_user_id_day" in index_names
        engine.dispose()

        command.downgrade(cfg, "0016")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("review_sessions")}
        assert "day" not in columns
        engine.dispose()
    finally:
        command.downgrade(cfg, "base")


def test_upgrade_head_creates_vocabulary_quiz_tables_then_downgrade_to_0017_removes_them():
    cfg = _alembic_config_for_test_db()
    command.upgrade(cfg, "head")
    try:
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "vocabulary_quizzes" in table_names
        assert "vocabulary_quiz_items" in table_names
        engine.dispose()

        command.downgrade(cfg, "0017")
        engine = create_engine(settings.TEST_DATABASE_URL)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "vocabulary_quizzes" not in table_names
        assert "vocabulary_quiz_items" not in table_names
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
        # passage_text moved to reading_passages (migration 0020 — see
        # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md).
        assert exercise_columns == {
            "id",
            "user_id",
            "day",
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
