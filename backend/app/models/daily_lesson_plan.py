import uuid
from datetime import date, datetime

from sqlalchemy import Date, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DailyFocus(Base):
    __tablename__ = "daily_focus"
    __table_args__ = (
        UniqueConstraint("day", "skill", name="uq_daily_focus_day_skill"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    skill: Mapped[str] = mapped_column(Text, nullable=False)
    focus_kind: Mapped[str] = mapped_column(Text, nullable=False)
    focus_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
