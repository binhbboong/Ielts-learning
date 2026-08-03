"""add day column to writing/speaking submissions; allow AI-generated speaking prompts

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("writing_submissions", sa.Column("day", sa.Date(), nullable=True))
    op.add_column("speaking_submissions", sa.Column("day", sa.Date(), nullable=True))
    op.add_column(
        "speaking_submissions", sa.Column("prompt_text", sa.Text(), nullable=True)
    )
    op.alter_column(
        "speaking_submissions", "question_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "speaking_submissions", "question_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False
    )
    op.drop_column("speaking_submissions", "prompt_text")
    op.drop_column("speaking_submissions", "day")
    op.drop_column("writing_submissions", "day")
