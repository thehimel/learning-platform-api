import logging
import sys

import structlog

from app.infra.logging.constants import LOG_TIMESTAMP_FORMAT, QUIET_LOGGER_NAMES

_shared_processors = [
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt=LOG_TIMESTAMP_FORMAT),
    structlog.processors.format_exc_info,
]


def configure_logging() -> None:
    """Configure structlog and stdlib logging once at startup, so both render as JSON through one pipeline."""
    structlog.configure(
        processors=[*_shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_shared_processors,
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, structlog.processors.JSONRenderer()],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    for logger_name in QUIET_LOGGER_NAMES:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structured logger. Always pass __name__ as the argument."""
    return structlog.get_logger(name)
