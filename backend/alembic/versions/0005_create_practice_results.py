"""create practice results

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "practice_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=False),
        sa.Column(
            "missed_question_types",
            postgresql.ARRAY(sa.String()),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "logged_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_practice_results_skill_logged_at",
        "practice_results",
        ["skill", "logged_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_practice_results_skill_logged_at",
        table_name="practice_results",
    )
    op.drop_table("practice_results")
