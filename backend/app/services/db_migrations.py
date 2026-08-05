"""Runs pending Alembic migrations against the currently configured database.

Exists so a deploy can apply its own migrations from inside the running
serverless function, using the DATABASE_URL Vercel already injects securely —
sidestepping getting a production connection string onto a local machine at
all (see docs/adr/DECISIONS.md 2026-08-05 entries for the exam-structure
migrations this was first needed for).
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

from app.core.config import settings

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    # Deliberately do not set sqlalchemy.url here: alembic/env.py already
    # falls back to settings.DATABASE_URL when it's unset, so this always
    # targets whatever database the running process is actually configured
    # for (real prod value in the deployed function, TEST_DATABASE_URL when
    # settings.DATABASE_URL is monkeypatched in tests).
    return cfg


def upgrade_to_head() -> str:
    """Runs `alembic upgrade head` and returns the resulting current revision
    (empty string if the database has no revision stamped, which shouldn't
    happen after a successful upgrade but is checked rather than assumed)."""
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.connect() as connection:
            heads = MigrationContext.configure(connection).get_current_heads()
    finally:
        engine.dispose()
    return heads[0] if heads else ""
