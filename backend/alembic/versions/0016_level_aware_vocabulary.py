"""add level metadata to vocabulary words

Revision ID: 0016
Revises: 0015
"""

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vocabulary_words", sa.Column("target_band", sa.Float(), nullable=True))
    op.add_column("vocabulary_words", sa.Column("cefr_level", sa.Text(), nullable=True))
    op.add_column(
        "vocabulary_words",
        sa.Column("source", sa.Text(), server_default="manual", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("vocabulary_words", "source")
    op.drop_column("vocabulary_words", "cefr_level")
    op.drop_column("vocabulary_words", "target_band")
