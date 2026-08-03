import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.user import LEGACY_USER_ID


class WritingSubmission(Base):
    __tablename__ = "writing_submissions"

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
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(5), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    task_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    coherence_and_cohesion: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lexical_resource: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    grammatical_range_and_accuracy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_band: Mapped[float | None] = mapped_column(Float, nullable=True)
    corrections: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    day: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
