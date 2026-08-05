"""split reading/listening exercises into passages/sections (standard-tier structure)

Revision ID: 0020
Revises: 0019
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Reading: reading_exercises.passage_text -> reading_passages ---
    op.create_table(
        "reading_passages",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "exercise_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reading_exercises.id"), nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("passage_text", sa.Text(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_reading_passages_exercise_id", "reading_passages", ["exercise_id"])

    op.execute(
        """
        INSERT INTO reading_passages (id, exercise_id, title, passage_text, "order")
        SELECT gen_random_uuid(), id, NULL, passage_text, 1 FROM reading_exercises
        """
    )

    op.add_column("reading_questions", sa.Column("passage_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("reading_questions", sa.Column("group_instructions", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE reading_questions rq SET passage_id = rp.id
        FROM reading_passages rp WHERE rp.exercise_id = rq.exercise_id
        """
    )
    op.alter_column("reading_questions", "passage_id", nullable=False)
    op.create_foreign_key(
        "fk_reading_questions_passage_id", "reading_questions", "reading_passages",
        ["passage_id"], ["id"],
    )
    op.drop_index("ix_reading_questions_exercise_id", table_name="reading_questions")
    op.drop_column("reading_questions", "exercise_id")
    op.drop_column("reading_exercises", "passage_text")

    # --- Listening: listening_exercises.{script_text,audio_*} -> listening_sections ---
    op.create_table(
        "listening_sections",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "exercise_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listening_exercises.id"), nullable=False,
        ),
        sa.Column("context_type", sa.Text(), nullable=False, server_default="monologue"),
        sa.Column("script_text", sa.Text(), nullable=False),
        sa.Column("audio_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("audio_content_type", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_listening_sections_exercise_id", "listening_sections", ["exercise_id"])

    op.execute(
        """
        INSERT INTO listening_sections
            (id, exercise_id, context_type, script_text, audio_bytes, audio_content_type, "order")
        SELECT gen_random_uuid(), id, 'monologue', script_text, audio_bytes, audio_content_type, 1
        FROM listening_exercises
        """
    )

    op.add_column("listening_questions", sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("listening_questions", sa.Column("group_instructions", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE listening_questions lq SET section_id = ls.id
        FROM listening_sections ls WHERE ls.exercise_id = lq.exercise_id
        """
    )
    op.alter_column("listening_questions", "section_id", nullable=False)
    op.create_foreign_key(
        "fk_listening_questions_section_id", "listening_questions", "listening_sections",
        ["section_id"], ["id"],
    )
    op.drop_index("ix_listening_questions_exercise_id", table_name="listening_questions")
    op.drop_column("listening_questions", "exercise_id")
    op.drop_column("listening_exercises", "script_text")
    op.drop_column("listening_exercises", "audio_bytes")
    op.drop_column("listening_exercises", "audio_content_type")


def downgrade() -> None:
    op.add_column("listening_exercises", sa.Column("script_text", sa.Text(), nullable=True))
    op.add_column("listening_exercises", sa.Column("audio_bytes", sa.LargeBinary(), nullable=True))
    op.add_column("listening_exercises", sa.Column("audio_content_type", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE listening_exercises le SET
            script_text = ls.script_text,
            audio_bytes = ls.audio_bytes,
            audio_content_type = ls.audio_content_type
        FROM listening_sections ls WHERE ls.exercise_id = le.id AND ls."order" = 1
        """
    )
    op.alter_column("listening_exercises", "script_text", nullable=False)

    op.add_column("listening_questions", sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        """
        UPDATE listening_questions lq SET exercise_id = ls.exercise_id
        FROM listening_sections ls WHERE ls.id = lq.section_id
        """
    )
    op.alter_column("listening_questions", "exercise_id", nullable=False)
    op.create_index("ix_listening_questions_exercise_id", "listening_questions", ["exercise_id"])
    op.drop_constraint("fk_listening_questions_section_id", "listening_questions", type_="foreignkey")
    op.drop_column("listening_questions", "section_id")
    op.drop_column("listening_questions", "group_instructions")
    op.drop_index("ix_listening_sections_exercise_id", table_name="listening_sections")
    op.drop_table("listening_sections")

    op.add_column("reading_exercises", sa.Column("passage_text", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE reading_exercises re SET passage_text = rp.passage_text
        FROM reading_passages rp WHERE rp.exercise_id = re.id AND rp."order" = 1
        """
    )
    op.alter_column("reading_exercises", "passage_text", nullable=False)

    op.add_column("reading_questions", sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        """
        UPDATE reading_questions rq SET exercise_id = rp.exercise_id
        FROM reading_passages rp WHERE rp.id = rq.passage_id
        """
    )
    op.alter_column("reading_questions", "exercise_id", nullable=False)
    op.create_index("ix_reading_questions_exercise_id", "reading_questions", ["exercise_id"])
    op.drop_constraint("fk_reading_questions_passage_id", "reading_questions", type_="foreignkey")
    op.drop_column("reading_questions", "passage_id")
    op.drop_column("reading_questions", "group_instructions")
    op.drop_index("ix_reading_passages_exercise_id", table_name="reading_passages")
    op.drop_table("reading_passages")
