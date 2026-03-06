"""User domain errors: codes, exceptions, and HTTP handlers."""

from app.users.errors.handlers import register_user_exception_handlers
from app.users.errors.types import (
    CannotDeleteSelfError,
    UserErrorCode,
    UserNotFoundError,
)

__all__ = [
    "CannotDeleteSelfError",
    "UserErrorCode",
    "UserNotFoundError",
    "register_user_exception_handlers",
]
