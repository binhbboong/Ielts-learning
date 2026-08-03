import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.user import LEGACY_USER_ID


class SpeakingSubmission(Base):
    __tablename__ = "speaking_submissions"

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
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("speaking_questions.id"), nullable=True
    )
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    day: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    audio_storage_ref: Mapped[str] = mapped_column(Text, nullable=False)
    audio_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    fluency_and_coherence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lexical_resource: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    grammatical_range_and_accuracy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
        onupdate=text("now()"),
    )
