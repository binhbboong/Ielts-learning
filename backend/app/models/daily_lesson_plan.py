import uuid
from datetime import date, datetime

from sqlalchemy import Date, Float, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.user import LEGACY_USER_ID


class DailyFocus(Base):
    __tablename__ = "daily_focus"
    __table_args__ = (
        UniqueConstraint("user_id", "day", "skill", name="uq_daily_focus_user_day_skill"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        default=LEGACY_USER_ID,
        server_default=text("'00000000-0000-0000-0000-000000000001'::uuid"),
    )
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    skill: Mapped[str] = mapped_column(Text, nullable=False)
    focus_kind: Mapped[str] = mapped_column(Text, nullable=False)
    focus_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_band: Mapped[float] = mapped_column(Float, nullable=False, default=4.5)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    priority: Mapped[str] = mapped_column(Text, nullable=False, default="support")
    phase: Mapped[str] = mapped_column(Text, nullable=False, default="foundation")
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="Scheduled rotation")
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
