import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, LargeBinary, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.user import LEGACY_USER_ID


class ListeningExercise(Base):
    __tablename__ = "listening_exercises"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_listening_exercises_user_day"),
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
    # question_type/accepted_answers added per
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
