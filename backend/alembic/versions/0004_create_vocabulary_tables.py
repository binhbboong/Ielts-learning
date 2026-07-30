"""create vocabulary tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _uuid_column(name: str):
    return sa.Column(
        name,
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        primary_key=True,
    )


def upgrade() -> None:
    op.create_table(
        "vocabulary_words",
        _uuid_column("id"),
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=False),
        sa.Column("example", sa.Text(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("interval_index", sa.Integer(), nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_vocabulary_words_next_due_date",
        "vocabulary_words",
        ["next_due_date"],
    )
    op.create_table(
        "review_sessions",
        _uuid_column("id"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_review_sessions_single_active "
        "ON review_sessions ((1)) WHERE completed_at IS NULL"
    )
    op.create_table(
        "review_session_items",
        _uuid_column("id"),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("review_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "word_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vocabulary_words.id"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "session_id", "position", name="uq_review_item_session_position"
        ),
        sa.UniqueConstraint(
            "session_id", "word_id", name="uq_review_item_session_word"
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('forgot', 'remembered')",
            name="ck_review_item_outcome",
        ),
    )


def downgrade() -> None:
    op.drop_table("review_session_items")
    op.drop_index(
        "uq_review_sessions_single_active", table_name="review_sessions"
    )
    op.drop_table("review_sessions")
    op.drop_index(
        "ix_vocabulary_words_next_due_date", table_name="vocabulary_words"
    )
    op.drop_table("vocabulary_words")
