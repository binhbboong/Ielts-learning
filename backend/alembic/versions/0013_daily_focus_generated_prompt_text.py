"""add generated_prompt_text column to daily_focus

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "daily_focus", sa.Column("generated_prompt_text", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("daily_focus", "generated_prompt_text")
