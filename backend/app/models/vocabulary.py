import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    word: Mapped[str] = mapped_column(Text, nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    example: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    interval_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ReviewSession(Base):
    __tablename__ = "review_sessions"
    __table_args__ = (
        Index(
            "uq_review_sessions_single_active",
            text("(1)"),
            unique=True,
            postgresql_where=text("completed_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    items: Mapped[list["ReviewSessionItem"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ReviewSessionItem(Base):
    __tablename__ = "review_session_items"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "position", name="uq_review_item_session_position"
        ),
        UniqueConstraint(
            "session_id", "word_id", name="uq_review_item_session_word"
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('forgot', 'remembered')",
            name="ck_review_item_outcome",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False
    )
    word_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vocabulary_words.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    session: Mapped[ReviewSession] = relationship(back_populates="items")
    word: Mapped[VocabularyWord] = relationship()
