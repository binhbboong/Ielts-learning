from datetime import datetime, timezone

from app.models.study_plan import PlanState, StudySkill, Task, TaskStatus
from app.services.study_plan import (
    get_plan_state,
    get_task,
    get_tasks_for_day,
    move_to_next_day,
    set_task_status,
    update_task_details,
    update_task_note,
)


def _seed(db_session):
    db_session.add(PlanState(id=1, current_day_number=3, total_days=180))
    db_session.add_all(
        [
            Task(
                day_number=day,
                skill=StudySkill.grammar,
                title=f"Day {day}",
                description="Original",
                estimated_minutes=20,
                status=TaskStatus.not_started,
                note="",
                updated_at=datetime.now(timezone.utc),
            )
            for day in (1, 3, 3)
        ]
    )
    db_session.commit()


def test_reads_plan_state_current_day_tasks_and_past_day_tasks(db_session):
    _seed(db_session)

    assert get_plan_state(db_session).current_day_number == 3
    assert len(get_tasks_for_day(db_session, 3)) == 2
    assert len(get_tasks_for_day(db_session, 1)) == 1
    task = get_tasks_for_day(db_session, 1)[0]
    assert get_task(db_session, task.id).id == task.id


def test_status_transitions_persist_without_advancing_day(db_session):
    _seed(db_session)
    task = get_tasks_for_day(db_session, 3)[0]

    for status in (
        TaskStatus.completed,
        TaskStatus.skipped,
        TaskStatus.not_started,
    ):
        assert set_task_status(db_session, task.id, status).status == status
        db_session.expire_all()
        assert get_task(db_session, task.id).status == status
        assert get_plan_state(db_session).current_day_number == 3


def test_note_and_details_updates_persist_without_advancing_day(db_session):
    _seed(db_session)
    task = get_tasks_for_day(db_session, 3)[0]

    update_task_note(db_session, task.id, "Review this pattern.")
    update_task_details(db_session, task.id, "Edited description", 35)
    db_session.expire_all()

    stored = get_task(db_session, task.id)
    assert stored.note == "Review this pattern."
    assert stored.description == "Edited description"
    assert stored.estimated_minutes == 35
    assert get_plan_state(db_session).current_day_number == 3


def test_move_to_next_day_is_blocked_by_unresolved_tasks(db_session):
    _seed(db_session)
    tasks = get_tasks_for_day(db_session, 3)
    set_task_status(db_session, tasks[0].id, TaskStatus.completed)

    result = move_to_next_day(db_session)

    assert result.blocked is True
    assert result.unresolved_task_ids == [tasks[1].id]
    assert result.current_day_number == 3
    assert get_plan_state(db_session).current_day_number == 3


def test_move_to_next_day_advances_and_preserves_past_tasks(
    db_session_factory,
):
    with db_session_factory() as first_session:
        _seed(first_session)
        tasks = get_tasks_for_day(first_session, 3)
        task_ids = [task.id for task in tasks]
        set_task_status(first_session, tasks[0].id, TaskStatus.completed)
        set_task_status(first_session, tasks[1].id, TaskStatus.skipped)

        result = move_to_next_day(first_session)

    assert result.blocked is False
    assert result.unresolved_task_ids == []
    assert result.current_day_number == 4
    with db_session_factory() as fresh_session:
        assert get_plan_state(fresh_session).current_day_number == 4
        assert [task.id for task in get_tasks_for_day(fresh_session, 3)] == [
            task_id for task_id in task_ids
        ]
