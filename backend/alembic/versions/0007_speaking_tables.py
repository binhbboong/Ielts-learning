"""create and seed speaking tables

Revision ID: 0007
Revises: 0006
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

QUESTIONS = (
    ("11111111-1111-1111-1111-111111111111", "PART_1", "What do you enjoy doing in your free time?"),
    ("22222222-2222-2222-2222-222222222222", "PART_1", "Tell me about the place where you live."),
    ("33333333-3333-3333-3333-333333333333", "PART_2", "Describe a skill you would like to learn. You should say what it is, why you want to learn it, and how you would learn it."),
    ("44444444-4444-4444-4444-444444444444", "PART_2", "Describe a memorable journey you have taken."),
    ("55555555-5555-5555-5555-555555555555", "PART_3", "How has technology changed the way people learn new skills?"),
    ("66666666-6666-6666-6666-666666666666", "PART_3", "What should cities do to improve public transport?"),
)


def upgrade() -> None:
    questions = op.create_table(
        "speaking_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("part", sa.String(length=6), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False, unique=True),
        sa.CheckConstraint("part IN ('PART_1','PART_2','PART_3')", name="ck_speaking_question_part"),
    )
    op.bulk_insert(
        questions,
        [{"id": item[0], "part": item[1], "prompt": item[2]} for item in QUESTIONS],
    )
    op.create_table(
        "speaking_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("speaking_questions.id"), nullable=False),
        sa.Column("audio_storage_ref", sa.Text(), nullable=False),
        sa.Column("audio_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("fluency_and_coherence", postgresql.JSONB(), nullable=True),
        sa.Column("lexical_resource", postgresql.JSONB(), nullable=True),
        sa.Column("grammatical_range_and_accuracy", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('PROCESSING','TRANSCRIPTION_FAILED','EVALUATION_FAILED','COMPLETED')", name="ck_speaking_submission_status"),
    )


def downgrade() -> None:
    op.drop_table("speaking_submissions")
    op.drop_table("speaking_questions")
