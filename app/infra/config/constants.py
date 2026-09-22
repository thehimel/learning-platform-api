"""Constants for the config module: env-var defaults and the startup validation-error message."""

DEFAULT_POSTGRES_HOST = "localhost"
DEFAULT_POSTGRES_PORT = "5432"
DEFAULT_POSTGRES_DB = "learning-platform"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 1440
DEFAULT_JWT_TOKEN_TYPE = "bearer"
DEFAULT_AUTH_DUMMY_PASSWORD = "timing-equaliser-only"

ENV_ERROR_TYPE_MISSING = "missing"
ENV_ERROR_MESSAGE = "Missing: {missing}. Set in .env. See .env.example."
