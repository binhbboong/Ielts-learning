"""add per-user ownership and IELTS Academic study profiles

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

LEGACY_USER_ID = "00000000-0000-0000-0000-000000000001"
OWNED_TABLES = (
    "mistakes",
    "vocabulary_words",
    "review_sessions",
    "practice_results",
    "writing_submissions",
    "speaking_submissions",
    "reading_exercises",
    "listening_exercises",
    "daily_focus",
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """INSERT INTO users (id, email, display_name, password_hash)
            VALUES (:id, 'learner@legacy.local', 'Legacy learner', 'migrated')
            ON CONFLICT (email) DO NOTHING"""
        ).bindparams(id=LEGACY_USER_ID)
    )
    for table in OWNED_TABLES:
        op.add_column(
            table,
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text(f"'{LEGACY_USER_ID}'::uuid"),
                nullable=False,
            ),
        )
        op.create_foreign_key(
            f"fk_{table}_user_id",
            table,
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])

    op.drop_constraint("uq_daily_focus_day_skill", "daily_focus", type_="unique")
    op.create_unique_constraint(
        "uq_daily_focus_user_day_skill",
        "daily_focus",
        ["user_id", "day", "skill"],
    )
    op.drop_constraint("uq_reading_exercises_day", "reading_exercises", type_="unique")
    op.create_unique_constraint(
        "uq_reading_exercises_user_day",
        "reading_exercises",
        ["user_id", "day"],
    )
    op.drop_constraint("uq_listening_exercises_day", "listening_exercises", type_="unique")
    op.create_unique_constraint(
        "uq_listening_exercises_user_day",
        "listening_exercises",
        ["user_id", "day"],
    )
    op.drop_index("uq_review_sessions_single_active", table_name="review_sessions")
    op.create_index(
        "uq_review_sessions_single_active",
        "review_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )

    op.add_column("daily_focus", sa.Column("target_band", sa.Float(), nullable=False, server_default="4.5"))
    op.add_column("daily_focus", sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="25"))
    op.add_column("daily_focus", sa.Column("priority", sa.Text(), nullable=False, server_default="support"))
    op.add_column("daily_focus", sa.Column("phase", sa.Text(), nullable=False, server_default="foundation"))
    op.add_column("daily_focus", sa.Column("rationale", sa.Text(), nullable=False, server_default="Scheduled rotation"))

    op.create_table(
        "study_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_type", sa.String(32), nullable=False),
        sa.Column("baseline_band", sa.Float(), nullable=False),
        sa.Column("target_band", sa.Float(), nullable=False),
        sa.Column("minimum_skill_band", sa.Float(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("study_days_per_week", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.execute(
        sa.text(
            """INSERT INTO study_profiles
            (user_id, exam_type, baseline_band, target_band, minimum_skill_band,
             start_date, target_date, daily_minutes, study_days_per_week)
            VALUES (:id, 'ielts_academic', 3.5, 6.5, 6.0,
                    DATE '2026-07-30', DATE '2027-01-14', 60, 5)"""
        ).bindparams(id=LEGACY_USER_ID)
    )


def downgrade() -> None:
    op.drop_table("study_profiles")
    for column in ("rationale", "phase", "priority", "estimated_minutes", "target_band"):
        op.drop_column("daily_focus", column)
    op.drop_constraint("uq_daily_focus_user_day_skill", "daily_focus", type_="unique")
    op.create_unique_constraint("uq_daily_focus_day_skill", "daily_focus", ["day", "skill"])
    op.drop_constraint("uq_reading_exercises_user_day", "reading_exercises", type_="unique")
    op.create_unique_constraint("uq_reading_exercises_day", "reading_exercises", ["day"])
    op.drop_constraint("uq_listening_exercises_user_day", "listening_exercises", type_="unique")
    op.create_unique_constraint("uq_listening_exercises_day", "listening_exercises", ["day"])
    op.drop_index("uq_review_sessions_single_active", table_name="review_sessions")
    op.create_index(
        "uq_review_sessions_single_active",
        "review_sessions",
        [sa.text("(1)")],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )
    for table in reversed(OWNED_TABLES):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_constraint(f"fk_{table}_user_id", table, type_="foreignkey")
        op.drop_column(table, "user_id")
