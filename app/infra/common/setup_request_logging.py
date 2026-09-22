"""Logs method, path, status code, and duration for every request."""

import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.infra.common.constants import REQUEST_COMPLETED_EVENT, REQUEST_DURATION_DECIMAL_PLACES
from app.infra.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started_at = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            REQUEST_COMPLETED_EVENT,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(elapsed_ms, REQUEST_DURATION_DECIMAL_PLACES),
        )
        return response


def setup_request_logging(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)
