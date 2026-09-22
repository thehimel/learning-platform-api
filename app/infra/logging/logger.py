import logging
import sys

from app.infra.logging.constants import LOG_DATE_FORMAT, LOG_FORMAT, QUIET_LOGGER_NAMES


def configure_logging() -> None:
    """Configure root logging once at application startup."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout,
    )
    for logger_name in QUIET_LOGGER_NAMES:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Always pass __name__ as the argument."""
    return logging.getLogger(name)
