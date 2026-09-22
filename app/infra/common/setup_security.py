"""Adds a baseline set of security response headers to every response.

No Content-Security-Policy is set here: a strict default would break the Swagger UI at /docs,
which loads its assets from a CDN, so CSP is left for the app to opt into deliberately if needed.
"""

from fastapi import FastAPI
from secure import (
    CrossOriginOpenerPolicy,
    ReferrerPolicy,
    Secure,
    StrictTransportSecurity,
    XContentTypeOptions,
    XFrameOptions,
)
from secure.middleware import SecureASGIMiddleware

from app.infra.common.constants import HSTS_MAX_AGE_SECONDS

_secure_headers = Secure(
    xcto=XContentTypeOptions().nosniff(),
    xfo=XFrameOptions().deny(),
    referrer=ReferrerPolicy().strict_origin_when_cross_origin(),
    hsts=StrictTransportSecurity().max_age(HSTS_MAX_AGE_SECONDS).include_subdomains(),
    coop=CrossOriginOpenerPolicy().same_origin(),
)


def setup_security_headers(app: FastAPI) -> None:
    app.add_middleware(SecureASGIMiddleware, secure=_secure_headers)
