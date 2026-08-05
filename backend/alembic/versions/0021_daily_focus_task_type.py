"""add daily_focus.task_type (Writing Task 1/Task 2 alternation)

Revision ID: 0021
Revises: 0020
"""

from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("daily_focus", sa.Column("task_type", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("daily_focus", "task_type")
