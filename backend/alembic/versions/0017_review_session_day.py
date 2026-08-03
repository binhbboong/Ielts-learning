"""add day column to review_sessions for once-per-day backfill tracking

Revision ID: 0017
Revises: 0016
"""

from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "review_sessions",
        sa.Column(
            "day",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_review_sessions_user_id_day", "review_sessions", ["user_id", "day"]
    )


def downgrade() -> None:
    op.drop_index("ix_review_sessions_user_id_day", table_name="review_sessions")
    op.drop_column("review_sessions", "day")
