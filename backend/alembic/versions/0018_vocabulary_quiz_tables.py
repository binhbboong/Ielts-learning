"""add vocabulary quiz tables (post-review checkpoint quiz)

Revision ID: 0018
Revises: 0017
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vocabulary_quizzes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text("'00000000-0000-0000-0000-000000000001'::uuid"),
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correct", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.UniqueConstraint("user_id", "day", name="uq_vocabulary_quiz_user_day"),
    )
    op.create_index(
        "ix_vocabulary_quizzes_day", "vocabulary_quizzes", ["day"]
    )

    op.create_table(
        "vocabulary_quiz_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "quiz_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vocabulary_quizzes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "word_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vocabulary_words.id"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_option_index", sa.Integer(), nullable=False),
        sa.Column("selected_option_index", sa.Integer(), nullable=True),
        sa.UniqueConstraint(
            "quiz_id", "position", name="uq_vocabulary_quiz_item_position"
        ),
    )


def downgrade() -> None:
    op.drop_table("vocabulary_quiz_items")
    op.drop_index("ix_vocabulary_quizzes_day", table_name="vocabulary_quizzes")
    op.drop_table("vocabulary_quizzes")
