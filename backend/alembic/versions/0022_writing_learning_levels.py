"""add Writing learning-level metadata

Revision ID: 0022
Revises: 0021
"""

from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "writing_submissions",
        sa.Column("exercise_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "writing_submissions",
        sa.Column("practice_level", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("writing_submissions", "practice_level")
    op.drop_column("writing_submissions", "exercise_type")
