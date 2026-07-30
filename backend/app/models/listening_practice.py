import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, LargeBinary, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ListeningExercise(Base):
    __tablename__ = "listening_exercises"
    __table_args__ = (UniqueConstraint("day", name="uq_listening_exercises_day"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    audio_content_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    focus_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )


class ListeningQuestion(Base):
    __tablename__ = "listening_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listening_exercises.id"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(ARRAY(Text), nullable=False)
    correct_option_index: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)


class ListeningSubmission(Base):
    __tablename__ = "listening_submissions"
    __table_args__ = (
        UniqueConstraint("exercise_id", name="uq_listening_submissions_exercise_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listening_exercises.id"), nullable=False
    )
    answers: Mapped[list] = mapped_column(JSONB, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
