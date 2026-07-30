"""create writing submissions and AI call log

Revision ID: 0006
Revises: 0005
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "writing_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("task_type", sa.String(length=5), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("task_response", postgresql.JSONB(), nullable=True),
        sa.Column("coherence_and_cohesion", postgresql.JSONB(), nullable=True),
        sa.Column("lexical_resource", postgresql.JSONB(), nullable=True),
        sa.Column("grammatical_range_and_accuracy", postgresql.JSONB(), nullable=True),
        sa.Column("overall_band", sa.Float(), nullable=True),
        sa.Column("corrections", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "ai_call_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("writing_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("called_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ai_call_log")
    op.drop_table("writing_submissions")
