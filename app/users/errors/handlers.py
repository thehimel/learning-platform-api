"""HTTP handlers for user domain exceptions."""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_users.exceptions import UserNotExists

from .types import CannotDeleteSelfError, UserError, UserErrorCode, UserNotFoundError
from app.exceptions import error_detail


def _json_response(status_code: int, detail: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def user_error_handler(_request: Request, exc: UserError) -> JSONResponse:
    """Generic handler for all UserError subclasses. Metadata lives on the exception."""
    detail = error_detail(exc.error_code, exc.get_http_message(), **exc.get_extra_detail())
    return _json_response(exc.status_code, detail)


async def user_not_exists_handler(_request: Request, _exc: UserNotExists) -> JSONResponse:
    """Map fastapi-users UserNotExists to our user domain error format."""
    detail = error_detail(UserErrorCode.user_not_found, "User not found.")
    return _json_response(404, detail)


def register_user_exception_handlers(app) -> None:
    """Register all user domain exception handlers on the FastAPI app."""
    for exc_cls in (CannotDeleteSelfError, UserNotFoundError):
        app.add_exception_handler(exc_cls, user_error_handler)
    app.add_exception_handler(UserNotExists, user_not_exists_handler)
