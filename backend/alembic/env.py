import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.db import Base  # noqa: E402

# Import every epic's models here so Base.metadata knows about all tables
# (needed for autogenerate support later; hand-written migrations don't
# strictly require it, but keeping this current avoids surprises).
from app.models import access_protection  # noqa: E402,F401
from app.models import mistake  # noqa: E402,F401
from app.models import vocabulary  # noqa: E402,F401
from app.models import practice_result  # noqa: E402,F401
from app.models import writing_submission  # noqa: E402,F401
from app.models import ai_call_log  # noqa: E402,F401
from app.models import speaking_question  # noqa: E402,F401
from app.models import speaking_submission  # noqa: E402,F401
from app.models import reading_practice  # noqa: E402,F401
from app.models import listening_practice  # noqa: E402,F401
from app.models import daily_lesson_plan  # noqa: E402,F401
from app.models import user  # noqa: E402,F401
from app.models import study_profile  # noqa: E402,F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# Only default to DATABASE_URL if the caller hasn't already set a url
# (e.g. tests programmatically point this at TEST_DATABASE_URL instead).
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
