import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PracticeResult(Base):
    __tablename__ = "practice_results"
    __table_args__ = (
        Index(
            "ix_practice_results_skill_logged_at",
            "skill",
            "logged_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    skill: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    missed_question_types: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
