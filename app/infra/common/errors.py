"""Shared domain error base that every module's own error classes extend."""

from enum import Enum
from typing import Any

from fastapi import status


def error_detail(code: Enum | str, message: str, **extra: Any) -> dict[str, Any]:
    """Build the structured error detail dict every error response shares.

    code may be a domain error code enum (e.g. CourseErrorCode) or a plain string.
    """
    code_value = code.value if isinstance(code, Enum) else code
    return {"code": code_value, "message": message, **extra}


class DomainError(Exception):
    """Base for domain exceptions. Subclasses define status_code, error_code, message."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: Enum
    message: str = ""

    def get_http_message(self) -> str:
        """Message for HTTP response. Uses str(self) when exception was raised with custom message."""
        return str(self) if self.args else self.message

    def get_extra_detail(self) -> dict[str, Any]:
        """Extra fields for error_detail (e.g. missing_ids). Override in subclasses as needed."""
        return {}
