import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.infra.config import settings
from app.infra.database.constants import DATABASE_DRIVER, DATABASE_POOL_PRE_PING

DATABASE_URL = (
    f"{DATABASE_DRIVER}://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)


def build_connect_args() -> dict:
    """Connection kwargs for the DB driver. Reused by Alembic so both connect the same way."""
    return {"ssl": ssl.create_default_context()} if settings.postgres_ssl_require else {}


Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    connect_args=build_connect_args(),
    pool_pre_ping=DATABASE_POOL_PRE_PING,
    echo=settings.sql_echo,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session
