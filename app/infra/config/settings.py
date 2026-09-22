import os
import signal
import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infra.common.constants import CORS_ALLOW_ALL
from app.infra.config.constants import (
    DEFAULT_AUTH_DUMMY_PASSWORD,
    DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_JWT_ALGORITHM,
    DEFAULT_JWT_TOKEN_TYPE,
    DEFAULT_POSTGRES_DB,
    DEFAULT_POSTGRES_HOST,
    DEFAULT_POSTGRES_PORT,
    ENV_ERROR_MESSAGE,
    ENV_ERROR_TYPE_MISSING,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_host: str = DEFAULT_POSTGRES_HOST
    postgres_port: str = DEFAULT_POSTGRES_PORT
    postgres_db: str = DEFAULT_POSTGRES_DB
    postgres_ssl_require: bool = False  # true for Neon and other cloud Postgres
    postgres_db_test: str | None = None  # falls back to {postgres_db}_test
    sql_echo: bool = False

    # Must be non-empty, or hashing is fast enough to leak login timing when a user is not found.
    auth_dummy_password: str = DEFAULT_AUTH_DUMMY_PASSWORD

    # openssl rand -hex 32
    auth_reset_password_token_secret: str
    auth_verification_token_secret: str

    # openssl rand -hex 32
    jwt_secret_key: str
    jwt_algorithm: str = DEFAULT_JWT_ALGORITHM
    jwt_access_token_expire_minutes: int = DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES  # 1 day
    jwt_token_type: str = DEFAULT_JWT_TOKEN_TYPE

    cors_origins: str = CORS_ALLOW_ALL  # "*" or a comma-separated list

    rating_recompute_async: bool = True
    rate_limit_enabled: bool = True


try:
    settings = Settings()
except ValidationError as e:
    missing = [str(err["loc"][0]).upper() for err in e.errors() if err["type"] == ENV_ERROR_TYPE_MISSING]
    print(ENV_ERROR_MESSAGE.format(missing=", ".join(missing)), file=sys.stderr)
    try:
        os.kill(os.getppid(), signal.SIGTERM)
    except OSError:
        pass
    sys.exit(1)
