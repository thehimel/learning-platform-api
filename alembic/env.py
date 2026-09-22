import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from app.infra.database import Base, DATABASE_URL, build_connect_args

# Import all models here so their tables register with Base.metadata
# and alembic autogenerate can detect schema changes.
from app.courses import models as courses_models  # noqa: F401
from app.users import models as users_models  # noqa: F401

config = context.config

# Override the URL from settings so credentials are never hardcoded.
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Sync callback invoked inside the async engine connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations via run_sync."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        connect_args=build_connect_args(),
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
