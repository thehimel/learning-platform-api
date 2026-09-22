"""Domain error classes for the auth module."""

from enum import Enum

from fastapi import status

from app.infra.common.errors import DomainError


class AuthErrorCode(str, Enum):
    insufficient_permissions = "insufficient_permissions"


class AuthError(DomainError):
    """Base for auth domain exceptions. Subclasses define status_code, error_code, message."""

    error_code: AuthErrorCode


class InsufficientPermissionsError(AuthError):
    """Raised when the user's role does not satisfy the required permission."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = AuthErrorCode.insufficient_permissions
    message = "Insufficient permissions."
