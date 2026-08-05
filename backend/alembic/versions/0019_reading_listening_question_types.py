"""add question_type/accepted_answers to reading/listening questions; nullable options

Revision ID: 0019
Revises: 0018
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("reading_questions", "listening_questions"):
        op.add_column(
            table,
            sa.Column(
                "question_type",
                sa.Text(),
                nullable=False,
                server_default="multiple_choice",
            ),
        )
        op.add_column(
            table,
            sa.Column("accepted_answers", postgresql.ARRAY(sa.Text()), nullable=True),
        )
        op.alter_column(table, "options", existing_type=postgresql.ARRAY(sa.Text()), nullable=True)
        op.alter_column(
            table, "correct_option_index", existing_type=sa.Integer(), nullable=True
        )


def downgrade() -> None:
    for table in ("reading_questions", "listening_questions"):
        # The pre-0019 schema is option-based only (every question has a
        # correct_option_index into options). Text-based questions
        # (note_completion, summary_completion, ...) have no representation
        # there — delete them explicitly rather than letting the NOT NULL
        # restores below fail with a constraint violation the first time any
        # such question exists.
        op.execute(
            f"""
            DELETE FROM {table}
            WHERE correct_option_index IS NULL OR options IS NULL
            """
        )
        op.alter_column(
            table, "correct_option_index", existing_type=sa.Integer(), nullable=False
        )
        op.alter_column(table, "options", existing_type=postgresql.ARRAY(sa.Text()), nullable=False)
        op.drop_column(table, "accepted_answers")
        op.drop_column(table, "question_type")
