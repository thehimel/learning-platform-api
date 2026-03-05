# Async SQLAlchemy and Alembic Setup

Notes on how this project's async SQLAlchemy and Alembic setup differs from a sync one, and what to watch for.

## What's Different From a Sync Setup

- Driver: `asyncpg` instead of `psycopg2-binary`, so the URL scheme is `postgresql+asyncpg://`.
- Engine and session: `create_async_engine` and `AsyncSession` (via `async_sessionmaker`) instead of `create_engine` and `Session`. See [app/infra/database/database.py](../../app/infra/database/database.py).
- `get_db()` is an async generator, injected the same way as a sync one via `Depends`.
- Route handlers use `async def` and `await db.execute(...)` instead of `db.query(...)`.
- `expire_on_commit=False` is required in async mode. Without it, accessing a model attribute after `session.commit()` triggers a lazy load, which async SQLAlchemy does not support.
- Alembic itself is sync-only. [alembic/env.py](../../alembic/env.py) bridges it with `asyncio.run()` and SQLAlchemy's `run_sync()`.
- Every module's models must be imported in `alembic/env.py` so their tables register on `Base.metadata` before autogenerate runs. New modules need a `from app.<module> import models as <module>_models  # noqa: F401` line added there.

## Commands

```shell
# Generate a migration from model changes
alembic revision --autogenerate -m "message"

# Apply pending migrations
alembic upgrade head
```

See [commands.md](../commands.md) for the full Alembic command list.

## References

- [SQLAlchemy: Asyncio Extension](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy: Avoiding Lazy Loads in Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads)
- [Alembic: Using Asyncio With Alembic](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)
