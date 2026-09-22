"""Constants for the logging module: log line format and third-party loggers to quiet."""

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
QUIET_LOGGER_NAMES = ("uvicorn.access", "sqlalchemy.engine")
