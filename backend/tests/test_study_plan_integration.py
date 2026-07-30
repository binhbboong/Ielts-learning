from datetime import datetime, timezone

from app.models.study_plan import PlanState, StudySkill, Task, TaskStatus
from app.services.study_plan import (
    get_plan_state,
    get_task,
    move_to_next_day,
    set_task_status,
    update_task_details,
    update_task_note,
)


def test_full_study_plan_cycle_persists_across_sessions(db_session_factory):
    with db_session_factory() as write_session:
        write_session.add(PlanState(id=1, current_day_number=1, total_days=180))
        write_session.add_all(
            [
                Task(
                    day_number=1,
                    skill=skill,
                    title=skill.value,
                    description="Original",
                    estimated_minutes=20,
                    status=TaskStatus.not_started,
                    note=None,
                    updated_at=datetime.now(timezone.utc),
                )
                for skill in (StudySkill.reading, StudySkill.writing)
            ]
        )
        write_session.commit()
        task_ids = [
            task.id
            for task in write_session.query(Task).order_by(Task.id).all()
        ]

        set_task_status(
            write_session, task_ids[0], TaskStatus.completed
        )
        update_task_note(write_session, task_ids[0], "Review inference.")
        update_task_details(
            write_session, task_ids[0], "Edited practice", 45
        )
        set_task_status(write_session, task_ids[1], TaskStatus.skipped)
        result = move_to_next_day(write_session)
        assert result.blocked is False

    with db_session_factory() as read_session:
        stored = get_task(read_session, task_ids[0])
        assert stored.status == TaskStatus.completed
        assert stored.note == "Review inference."
        assert stored.description == "Edited practice"
        assert stored.estimated_minutes == 45
        assert get_plan_state(read_session).current_day_number == 2
