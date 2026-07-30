"""create reading practice tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reading_exercises",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("passage_text", sa.Text(), nullable=False),
        sa.Column("focus_reference", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("day", name="uq_reading_exercises_day"),
    )
    op.create_index(
        "ix_reading_exercises_day", "reading_exercises", ["day"]
    )

    op.create_table(
        "reading_questions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reading_exercises.id"),
            nullable=False,
        ),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("correct_option_index", sa.Integer(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_reading_questions_exercise_id", "reading_questions", ["exercise_id"]
    )

    op.create_table(
        "reading_submissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reading_exercises.id"),
            nullable=False,
        ),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("exercise_id", name="uq_reading_submissions_exercise_id"),
    )


def downgrade() -> None:
    op.drop_table("reading_submissions")
    op.drop_index("ix_reading_questions_exercise_id", table_name="reading_questions")
    op.drop_table("reading_questions")
    op.drop_index("ix_reading_exercises_day", table_name="reading_exercises")
    op.drop_table("reading_exercises")
