"""Adds a baseline set of security response headers to every response.

No Content-Security-Policy is set here: a strict default would break the Swagger UI at /docs,
which loads its assets from a CDN, so CSP is left for the app to opt into deliberately if needed.
"""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.infra.common.constants import SECURITY_HEADERS


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


def setup_security_headers(app: FastAPI) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
