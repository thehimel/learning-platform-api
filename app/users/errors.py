"""Domain error classes for the users module."""

from enum import Enum

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi_users.exceptions import UserNotExists

from app.infra.common.errors import DomainError, error_detail


class UserErrorCode(str, Enum):
    user_not_found = "user_not_found"
    cannot_delete_self = "cannot_delete_self"


class UserError(DomainError):
    """Base for user domain exceptions. Subclasses define status_code, error_code, message."""

    error_code: UserErrorCode


class UserNotFoundError(UserError):
    """Raised when a user does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = UserErrorCode.user_not_found
    message = "User not found."


class CannotDeleteSelfError(UserError):
    """Raised when a user attempts to delete their own account."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = UserErrorCode.cannot_delete_self
    message = "You cannot delete your own account."


async def _user_not_exists_handler(_request: Request, _exc: UserNotExists) -> JSONResponse:
    """Map fastapi-users' UserNotExists onto this module's own not-found error format."""
    detail = error_detail(UserErrorCode.user_not_found, UserNotFoundError.message)
    return JSONResponse(status_code=UserNotFoundError.status_code, content={"detail": detail})


def register_user_exception_handlers(app: FastAPI) -> None:
    """Map fastapi-users' UserNotExists to this module's format; DomainError subclasses are handled generically."""
    app.add_exception_handler(UserNotExists, _user_not_exists_handler)
