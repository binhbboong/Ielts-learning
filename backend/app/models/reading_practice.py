import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.user import LEGACY_USER_ID


class ReadingExercise(Base):
    __tablename__ = "reading_exercises"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_reading_exercises_user_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, default=LEGACY_USER_ID,
        server_default=text("'00000000-0000-0000-0000-000000000001'::uuid"),
    )
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    passage_text: Mapped[str] = mapped_column(Text, nullable=False)
    focus_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )


class ReadingQuestion(Base):
    __tablename__ = "reading_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reading_exercises.id"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(ARRAY(Text), nullable=False)
    correct_option_index: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)


class ReadingSubmission(Base):
    __tablename__ = "reading_submissions"
    __table_args__ = (
        UniqueConstraint("exercise_id", name="uq_reading_submissions_exercise_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reading_exercises.id"), nullable=False
    )
    answers: Mapped[list] = mapped_column(JSONB, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
