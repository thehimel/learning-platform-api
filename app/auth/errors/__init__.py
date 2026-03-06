"""Auth domain errors: codes, exceptions, and HTTP handlers."""

from app.auth.errors.handlers import register_auth_exception_handlers
from app.auth.errors.types import (
    AuthErrorCode,
    InsufficientPermissionsError,
)

__all__ = [
    "AuthErrorCode",
    "InsufficientPermissionsError",
    "register_auth_exception_handlers",
]
