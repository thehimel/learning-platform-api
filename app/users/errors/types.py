"""Exception classes and error codes for the users domain."""

from enum import Enum
from typing import Any


class UserErrorCode(str, Enum):
    user_not_found = "user_not_found"
    cannot_delete_self = "cannot_delete_self"


class UserError(Exception):
    """Base for user domain exceptions. Subclasses define status_code, error_code, message."""

    status_code: int = 500
    error_code: UserErrorCode
    message: str = ""

    def get_http_message(self) -> str:
        """Message for HTTP response. Uses str(self) when exception was raised with custom message."""
        return str(self) if self.args else self.message

    def get_extra_detail(self) -> dict[str, Any]:
        """Extra fields for error_detail. Override in subclasses as needed."""
        return {}


class UserNotFoundError(UserError):
    """Raised when a user does not exist."""

    status_code = 404
    error_code = UserErrorCode.user_not_found
    message = "User not found."


class CannotDeleteSelfError(UserError):
    """Raised when a user attempts to delete their own account."""

    status_code = 403
    error_code = UserErrorCode.cannot_delete_self
    message = "You cannot delete your own account."
