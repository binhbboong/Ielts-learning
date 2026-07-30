"""create mistakes table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mistakes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("skill", sa.Text(), nullable=False),
        sa.Column("question_type", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("own_answer", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "reason_category",
            sa.Text(),
            server_default=sa.text("'not_sure_other'"),
            nullable=False,
        ),
        sa.Column(
            "logged_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_mistakes_logged_at", "mistakes", ["logged_at"]
    )
    op.create_index(
        "ix_mistakes_reason_category", "mistakes", ["reason_category"]
    )


def downgrade() -> None:
    op.drop_index("ix_mistakes_reason_category", table_name="mistakes")
    op.drop_index("ix_mistakes_logged_at", table_name="mistakes")
    op.drop_table("mistakes")
