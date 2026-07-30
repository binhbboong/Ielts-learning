from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.study_plan import StudySkill, TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_number: int
    skill: StudySkill
    title: str
    description: str
    estimated_minutes: int
    status: TaskStatus
    note: str | None
    updated_at: datetime


class PlanStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_day_number: int
    total_days: int


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskNoteUpdate(BaseModel):
    note: str | None = None


class TaskDetailsUpdate(BaseModel):
    description: str
    estimated_minutes: int = Field(gt=0)


class MoveToNextDayOut(BaseModel):
    blocked: bool
    unresolved_task_ids: list[int]
    current_day_number: int
