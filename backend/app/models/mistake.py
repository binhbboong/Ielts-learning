import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.user import LEGACY_USER_ID


class Mistake(Base):
    __tablename__ = "mistakes"

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
    skill: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    own_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_category: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'not_sure_other'"),
        index=True,
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )
