"""create study plan tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-29
"""

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


skill_enum = postgresql.ENUM(
    "grammar",
    "vocabulary",
    "listening",
    "reading",
    "speaking",
    "writing",
    "review",
    name="study_plan_skill",
    create_type=False,
)
status_enum = postgresql.ENUM(
    "not_started",
    "completed",
    "skipped",
    name="study_plan_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    skill_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("skill", skill_enum, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_day_number", "tasks", ["day_number"])
    op.create_table(
        "plan_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("current_day_number", sa.Integer(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_plan_state_singleton"),
    )


def downgrade() -> None:
    op.drop_table("plan_state")
    op.drop_index("ix_tasks_day_number", table_name="tasks")
    op.drop_table("tasks")
    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)
    skill_enum.drop(bind, checkfirst=True)
