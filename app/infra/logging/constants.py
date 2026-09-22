"""Constants for the logging module: structlog timestamp format and third-party loggers to quiet."""

LOG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
QUIET_LOGGER_NAMES = ("uvicorn.access", "sqlalchemy.engine")
