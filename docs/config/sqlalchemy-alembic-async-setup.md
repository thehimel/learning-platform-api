# Async SQLAlchemy + Alembic Setup

This guide covers setting up **async** SQLAlchemy with Alembic using `asyncpg` as the PostgreSQL driver.

---

## Overview: Sync vs Async Setup

| Aspect           | Sync setup                   | Async setup                          |
|------------------|------------------------------|--------------------------------------|
| Driver           | `psycopg2-binary`            | `asyncpg`                            |
| URL scheme       | `postgresql+psycopg2://`     | `postgresql+asyncpg://`              |
| Engine factory   | `create_engine`              | `create_async_engine`                |
| Session class    | `Session`                    | `AsyncSession`                       |
| Session factory  | `sessionmaker`               | `async_sessionmaker`                 |
| `get_db()`       | sync generator               | async generator                      |
| Alembic `env.py` | sync `run_migrations_online` | async via `asyncio.run` + `run_sync` |

---

## Step 1 — Update Dependencies

### `pyproject.toml`

Replace `psycopg2-binary` with `asyncpg`. The full updated file:

```
alembic
asyncpg
bcrypt
fastapi[all]
pre-commit
pydantic-settings
pytest
python-jose[cryptography]
ruff
sqlalchemy
```

Install:

```bash
uv sync
```

> Remove `psycopg2-binary` from `pyproject.toml` if present before running `uv sync`.

---

## Step 2 — Create `app/database.py`

This is the async equivalent of a standard sync `database.py`.

```python
# app/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

# Base class for all ORM models
Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Test connections before use to avoid stale sessions.
    echo=settings.sql_echo,   # Log SQL when SQL_ECHO=true in .env.
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # Prevents lazy-load errors after commit in async context.
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session
```

Key difference: `expire_on_commit=False` is important in async SQLAlchemy — without it, accessing model attributes after `session.commit()` would trigger a lazy load, which is not supported in async mode.

---

## Step 3 — Define a Model (Example)

Models are identical to the sync version — SQLAlchemy ORM model definitions do not change for async. The same `Base` import pattern applies.

```python
# app/courses/models.py
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    published = Column(Boolean, server_default="FALSE", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
```

After adding a model, **import it in `alembic/env.py`**:

```python
from app.courses import models as courses_models  # noqa: F401
```

This registers the table with `Base.metadata` so autogenerate can detect it.

---

## Step 4 — Create `alembic.ini`

Run `alembic init alembic` from the project root to regenerate the missing files, then update `alembic.ini`.

```bash
alembic init alembic
```

The `sqlalchemy.url` line is just a placeholder — it gets overridden at runtime in `env.py`.  
Update the placeholder to reflect the async driver:

```ini
# In alembic.ini, find and update:
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/dbname
```

> No other changes are needed in `alembic.ini`. All other defaults remain the same as a standard sync setup.

---

## Step 5 — Create `alembic/env.py`

This is the most changed file. Alembic itself is sync-only, so we use `asyncio.run()` + SQLAlchemy's `run_sync()` to bridge the async engine into the sync migration runner.

```python
# alembic/env.py
import asyncio
import sys
from pathlib import Path

# Add project root so we can import app modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from app.database import Base
from app.config import settings

# Import all models here so their tables register with Base.metadata
# and alembic autogenerate can detect schema changes.
# Example (uncomment as models are added):
# from app.courses import models as courses_models  # noqa: F401

config = context.config

# Override the URL from settings so credentials are never hardcoded.
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}",
)

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


def do_run_migrations(connection):
    """Sync callback invoked inside the async engine connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations via run_sync."""
    connectable = create_async_engine(config.get_main_option("sqlalchemy.url"))
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
```

### How this differs from a sync `alembic/env.py`

| Part          | Sync setup                             | Async setup                                |
|---------------|----------------------------------------|--------------------------------------------|
| Engine        | `engine_from_config(...)`              | `create_async_engine(...)`                 |
| Online runner | `with engine.connect() as connection:` | `async with engine.connect()` + `run_sync` |
| Entry point   | direct `context.configure(...)`        | `asyncio.run(run_async_migrations())`      |

---

## Step 6 — Using `get_db` in Route Handlers

Usage is the same as the sync version — just add `async` to the route function:

```python
# app/courses/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/")
async def get_courses(db: AsyncSession = Depends(get_db)):
    # Use `await db.execute(...)` instead of `db.query(...)`
    ...
```

---

## Step 7 — Alembic CLI Commands

These commands are identical between sync and async setups.

```bash
# Generate a new migration (autogenerate from model changes)
alembic revision --autogenerate -m "description of change"

# Example: generate initial migration for the courses table
alembic revision --autogenerate -m "create courses table"

# Apply all pending migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Show current migration state
alembic current

# Show migration history
alembic history
```

---

## Data Flow Diagram

```
.env
  └─→ app/config.py (pydantic Settings)
        └─→ app/database.py (async engine + Base + AsyncSessionLocal + get_db)
              └─→ app/courses/models.py ← inherit Base

alembic/env.py
  ├─ imports Base from app.database      (for target_metadata)
  ├─ imports models to register tables   (noqa: F401)
  ├─ builds async URL from settings      (overrides alembic.ini placeholder)
  └─ asyncio.run → run_sync → alembic migrations
```

---

## Summary Checklist

- [ ] Replace `psycopg2-binary` with `asyncpg` in `pyproject.toml`
- [ ] Create `app/database.py` using `create_async_engine` and `AsyncSession`
- [ ] Create model(s) inheriting from `Base` (e.g. `app/courses/models.py`)
- [ ] Run `alembic init alembic` (or manually recreate `alembic.ini` + `alembic/env.py`)
- [ ] Update `alembic.ini` placeholder URL to use `postgresql+asyncpg://`
- [ ] Replace `alembic/env.py` with the async-compatible version above
- [ ] Import all models in `alembic/env.py` before running migrations
- [ ] Use `async def` + `await db.execute(...)` in route handlers

---

## References

- [SQLAlchemy — Asyncio Extension](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy — Async Session](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads)
- [Alembic — Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Alembic — Async Migration Support](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)
- [asyncpg — GitHub](https://github.com/MagicStack/asyncpg)
- [pydantic-settings — Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
