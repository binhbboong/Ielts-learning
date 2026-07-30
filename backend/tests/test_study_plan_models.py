from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models.study_plan import PlanState, StudySkill, Task, TaskStatus


ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _alembic_config_for_test_db() -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "alembic")
    )
    return config


def test_migration_creates_study_plan_schema_enums_constraint_and_index():
    config = _alembic_config_for_test_db()
    command.upgrade(config, "head")
    engine = create_engine(settings.TEST_DATABASE_URL)
    try:
        inspector = inspect(engine)
        assert {"tasks", "plan_state"}.issubset(inspector.get_table_names())
        assert {column["name"] for column in inspector.get_columns("tasks")} == {
            "id",
            "day_number",
            "skill",
            "title",
            "description",
            "estimated_minutes",
            "status",
            "note",
            "updated_at",
        }
        assert {column["name"] for column in inspector.get_columns("plan_state")} == {
            "id",
            "current_day_number",
            "total_days",
        }
        assert "ix_tasks_day_number" in {
            index["name"] for index in inspector.get_indexes("tasks")
        }

        with engine.connect() as connection:
            enum_names = set(
                connection.execute(
                    text(
                        "SELECT typname FROM pg_type "
                        "WHERE typname IN ('study_plan_skill', 'study_plan_status')"
                    )
                ).scalars()
            )
        assert enum_names == {"study_plan_skill", "study_plan_status"}
    finally:
        engine.dispose()
        command.downgrade(config, "base")


def test_plan_state_rejects_any_non_singleton_id(db_session):
    db_session.add(PlanState(id=2, current_day_number=1, total_days=180))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_task_and_plan_state_round_trip_through_a_fresh_session(db_session_factory):
    updated_at = datetime.now(timezone.utc)
    write_session = db_session_factory()
    task = Task(
        day_number=12,
        skill=StudySkill.writing,
        title="Write Task 2 introduction",
        description="Draft and revise one introduction.",
        estimated_minutes=25,
        status=TaskStatus.not_started,
        note="Focus on paraphrasing.",
        updated_at=updated_at,
    )
    write_session.add_all(
        [task, PlanState(id=1, current_day_number=12, total_days=180)]
    )
    write_session.commit()
    task_id = task.id
    write_session.close()

    read_session = db_session_factory()
    stored_task = read_session.get(Task, task_id)
    stored_state = read_session.get(PlanState, 1)
    read_session.close()

    assert stored_task.day_number == 12
    assert stored_task.skill == StudySkill.writing
    assert stored_task.title == "Write Task 2 introduction"
    assert stored_task.description == "Draft and revise one introduction."
    assert stored_task.estimated_minutes == 25
    assert stored_task.status == TaskStatus.not_started
    assert stored_task.note == "Focus on paraphrasing."
    assert stored_task.updated_at == updated_at
    assert stored_state.current_day_number == 12
    assert stored_state.total_days == 180
