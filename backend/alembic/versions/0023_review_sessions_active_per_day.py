"""allow one active vocabulary review session per learner and day

Revision ID: 0023
Revises: 0022
"""

from alembic import op
import sqlalchemy as sa


revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("uq_review_sessions_single_active", table_name="review_sessions")
    op.create_index(
        "uq_review_sessions_single_active",
        "review_sessions",
        ["user_id", "day"],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_review_sessions_single_active", table_name="review_sessions")
    op.create_index(
        "uq_review_sessions_single_active",
        "review_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )
