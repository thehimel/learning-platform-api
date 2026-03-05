"""HTTP handlers for auth domain exceptions."""

from fastapi import Request
from fastapi.responses import JSONResponse

from .types import AuthError, InsufficientPermissionsError
from app.exceptions import error_detail


def _json_response(status_code: int, detail: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def auth_error_handler(_request: Request, exc: AuthError) -> JSONResponse:
    """Generic handler for all AuthError subclasses. Metadata lives on the exception."""
    detail = error_detail(exc.error_code, exc.get_http_message(), **exc.get_extra_detail())
    return _json_response(exc.status_code, detail)


def register_auth_exception_handlers(app) -> None:
    """Register all auth domain exception handlers on the FastAPI app."""
    app.add_exception_handler(InsufficientPermissionsError, auth_error_handler)
