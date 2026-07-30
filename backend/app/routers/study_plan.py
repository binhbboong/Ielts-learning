from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_learner
from app.schemas.study_plan import (
    MoveToNextDayOut,
    PlanStateOut,
    TaskDetailsUpdate,
    TaskNoteUpdate,
    TaskOut,
    TaskStatusUpdate,
)
from app.services import study_plan as service

router = APIRouter(
    prefix="/api/study-plan",
    dependencies=[Depends(require_learner)],
)


def _task_or_404(task):
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/state", response_model=PlanStateOut)
def read_plan_state(db: Session = Depends(get_db)):
    state = service.get_plan_state(db)
    if state is None:
        raise HTTPException(status_code=404, detail="Plan state not found")
    return state


@router.get("/days/{day_number}/tasks", response_model=list[TaskOut])
def read_day_tasks(day_number: int, db: Session = Depends(get_db)):
    return service.get_tasks_for_day(db, day_number)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def read_task(task_id: int, db: Session = Depends(get_db)):
    return _task_or_404(service.get_task(db, task_id))


@router.patch("/tasks/{task_id}/status", response_model=TaskOut)
def patch_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
):
    return _task_or_404(service.set_task_status(db, task_id, payload.status))


@router.patch("/tasks/{task_id}/note", response_model=TaskOut)
def patch_task_note(
    task_id: int,
    payload: TaskNoteUpdate,
    db: Session = Depends(get_db),
):
    return _task_or_404(service.update_task_note(db, task_id, payload.note))


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def patch_task_details(
    task_id: int,
    payload: TaskDetailsUpdate,
    db: Session = Depends(get_db),
):
    return _task_or_404(
        service.update_task_details(
            db,
            task_id,
            payload.description,
            payload.estimated_minutes,
        )
    )


@router.post("/move-to-next-day", response_model=MoveToNextDayOut)
def advance_plan(db: Session = Depends(get_db)):
    result = service.move_to_next_day(db)
    if result.blocked:
        raise HTTPException(
            status_code=409,
            detail={"unresolved_task_ids": result.unresolved_task_ids},
        )
    return result
