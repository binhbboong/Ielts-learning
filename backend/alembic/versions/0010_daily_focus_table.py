"""create daily_focus table

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_focus",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("skill", sa.Text(), nullable=False),
        sa.Column("focus_kind", sa.Text(), nullable=False),
        sa.Column("focus_reference", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("day", "skill", name="uq_daily_focus_day_skill"),
    )
    op.create_index("ix_daily_focus_day", "daily_focus", ["day"])


def downgrade() -> None:
    op.drop_index("ix_daily_focus_day", table_name="daily_focus")
    op.drop_table("daily_focus")
