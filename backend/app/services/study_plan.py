from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.study_plan import PlanState, Task, TaskStatus
from app.services.export_utils import serialize_all


@dataclass(frozen=True)
class MoveToNextDayResult:
    blocked: bool
    unresolved_task_ids: list[int]
    current_day_number: int


def get_plan_state(session: Session) -> PlanState | None:
    return session.get(PlanState, 1)


def get_tasks_for_day(session: Session, day_number: int) -> list[Task]:
    statement = (
        select(Task)
        .where(Task.day_number == day_number)
        .order_by(Task.id)
    )
    return list(session.scalars(statement))


def get_task(session: Session, task_id: int) -> Task | None:
    return session.get(Task, task_id)


def _persist_task(session: Session, task: Task) -> Task:
    task.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(task)
    return task


def set_task_status(
    session: Session, task_id: int, status: TaskStatus
) -> Task | None:
    task = get_task(session, task_id)
    if task is None:
        return None
    task.status = status
    return _persist_task(session, task)


def update_task_note(
    session: Session, task_id: int, note: str | None
) -> Task | None:
    task = get_task(session, task_id)
    if task is None:
        return None
    task.note = note
    return _persist_task(session, task)


def update_task_details(
    session: Session,
    task_id: int,
    description: str,
    estimated_minutes: int,
) -> Task | None:
    task = get_task(session, task_id)
    if task is None:
        return None
    task.description = description
    task.estimated_minutes = estimated_minutes
    return _persist_task(session, task)


def move_to_next_day(session: Session) -> MoveToNextDayResult:
    state = get_plan_state(session)
    if state is None:
        raise ValueError("Plan state has not been initialized")

    unresolved_ids = list(
        session.scalars(
            select(Task.id)
            .where(
                Task.day_number == state.current_day_number,
                Task.status == TaskStatus.not_started,
            )
            .order_by(Task.id)
        )
    )
    if unresolved_ids:
        return MoveToNextDayResult(
            blocked=True,
            unresolved_task_ids=unresolved_ids,
            current_day_number=state.current_day_number,
        )

    state.current_day_number += 1
    session.commit()
    session.refresh(state)
    return MoveToNextDayResult(
        blocked=False,
        unresolved_task_ids=[],
        current_day_number=state.current_day_number,
    )


def export_learner_data(session: Session) -> dict:
    return {
        "category": "study_plan",
        "plan_state": serialize_all(session, PlanState),
        "tasks": serialize_all(session, Task),
    }
