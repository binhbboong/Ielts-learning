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
    # passage_text lives on ReadingPassage now (1 passage at beginner tier, 2 at
    # standard tier) per docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
    focus_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )


class ReadingPassage(Base):
    __tablename__ = "reading_passages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reading_exercises.id"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    passage_text: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)


class ReadingQuestion(Base):
    __tablename__ = "reading_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    passage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reading_passages.id"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    # question_type/accepted_answers/group_instructions added per
    # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md. options/
    # correct_option_index are used by option-based types (multiple_choice,
    # true_false_not_given, matching, ...); accepted_answers is used by
    # text-based/completion types instead — see app.services.exam_question_types.
    question_type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="multiple_choice"
    )
    options: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    correct_option_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accepted_answers: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    group_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
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
