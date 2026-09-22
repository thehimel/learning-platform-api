"""The single handler that maps any exception to one HTTP error envelope, registered once for the app.

Every failure mode - a domain error, an HTTPException (including fastapi-users' own), a request
validation failure, or a genuinely unexpected bug - is resolved to the same {"detail": {"code",
"message", ...}} shape by one function, registered for each exception type below. FastAPI dispatches
by walking the exception's MRO, so a subclass of any of these is covered without a handler of its own.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.infra.common.constants import (
    HANDLED_EXCEPTION_LOG_MESSAGE,
    HTTP_ERROR_CODE,
    INTERNAL_SERVER_ERROR_CODE,
    INTERNAL_SERVER_ERROR_MESSAGE,
    UNHANDLED_EXCEPTION_LOG_MESSAGE,
    VALIDATION_ERROR_CODE,
    VALIDATION_ERROR_MESSAGE,
)
from app.infra.common.errors import DomainError, error_detail
from app.infra.logging.logger import get_logger

logger = get_logger(__name__)


def _resolve_domain_error(exc: DomainError) -> tuple[int, dict[str, Any]]:
    return exc.status_code, error_detail(exc.error_code, exc.get_http_message(), **exc.get_extra_detail())


def _resolve_http_exception(exc: StarletteHTTPException) -> tuple[int, dict[str, Any]]:
    if isinstance(exc.detail, dict):
        raw = dict(exc.detail)
        code = raw.pop("code", HTTP_ERROR_CODE)
        message = raw.pop("message", None) or raw.pop("reason", None) or str(code)
        return exc.status_code, error_detail(str(code), message, **raw)
    code = str(exc.detail) if exc.detail else HTTP_ERROR_CODE
    return exc.status_code, error_detail(code, code)


def _resolve_validation_error(exc: RequestValidationError) -> tuple[int, dict[str, Any]]:
    errors = jsonable_encoder(exc.errors())
    detail = error_detail(VALIDATION_ERROR_CODE, VALIDATION_ERROR_MESSAGE, errors=errors)
    return status.HTTP_422_UNPROCESSABLE_CONTENT, detail


def _resolve_unhandled_exception() -> tuple[int, dict[str, Any]]:
    detail = error_detail(INTERNAL_SERVER_ERROR_CODE, INTERNAL_SERVER_ERROR_MESSAGE)
    return status.HTTP_500_INTERNAL_SERVER_ERROR, detail


def _resolve(exc: Exception) -> tuple[int, dict[str, Any]]:
    if isinstance(exc, DomainError):
        return _resolve_domain_error(exc)
    if isinstance(exc, RequestValidationError):
        return _resolve_validation_error(exc)
    if isinstance(exc, StarletteHTTPException):
        return _resolve_http_exception(exc)
    return _resolve_unhandled_exception()


def _log_exception(exc: Exception, status_code: int, request: Request, detail: dict[str, Any]) -> None:
    if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(UNHANDLED_EXCEPTION_LOG_MESSAGE, request.method, request.url.path, exc_info=exc)
    else:
        logger.warning(HANDLED_EXCEPTION_LOG_MESSAGE, request.method, request.url.path, detail["code"])


async def _exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, detail = _resolve(exc)
    _log_exception(exc, status_code, request, detail)
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app: FastAPI) -> None:
    """Register the one handler, for every exception type it covers, so every failure gets the same envelope."""
    for exc_type in (DomainError, StarletteHTTPException, RequestValidationError, Exception):
        app.add_exception_handler(exc_type, _exception_handler)
