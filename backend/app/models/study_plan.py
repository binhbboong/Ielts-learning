from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StudySkill(str, Enum):
    grammar = "grammar"
    vocabulary = "vocabulary"
    listening = "listening"
    reading = "reading"
    speaking = "speaking"
    writing = "writing"
    review = "review"


class TaskStatus(str, Enum):
    not_started = "not_started"
    completed = "completed"
    skipped = "skipped"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    skill: Mapped[StudySkill] = mapped_column(
        SqlEnum(StudySkill, name="study_plan_skill"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SqlEnum(TaskStatus, name="study_plan_status"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PlanState(Base):
    __tablename__ = "plan_state"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_plan_state_singleton"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
