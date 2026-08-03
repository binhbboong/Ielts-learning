import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StudyProfile(Base):
    __tablename__ = "study_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    exam_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ielts_academic"
    )
    baseline_band: Mapped[float] = mapped_column(Float, nullable=False, default=3.5)
    target_band: Mapped[float] = mapped_column(Float, nullable=False, default=6.5)
    minimum_skill_band: Mapped[float] = mapped_column(Float, nullable=False, default=6.0)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    study_days_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
