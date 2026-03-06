"""Exception classes and error codes for the auth domain."""

from enum import Enum
from typing import Any


class AuthErrorCode(str, Enum):
    insufficient_permissions = "insufficient_permissions"


class AuthError(Exception):
    """Base for auth domain exceptions. Subclasses define status_code, error_code, message."""

    status_code: int = 500
    error_code: AuthErrorCode
    message: str = ""

    def get_http_message(self) -> str:
        """Message for HTTP response. Uses str(self) when exception was raised with custom message."""
        return str(self) if self.args else self.message

    def get_extra_detail(self) -> dict[str, Any]:
        """Extra fields for error_detail. Override in subclasses as needed."""
        return {}


class InsufficientPermissionsError(AuthError):
    """Raised when the user's role does not satisfy the required permission."""

    status_code = 403
    error_code = AuthErrorCode.insufficient_permissions
    message = "Insufficient permissions."
