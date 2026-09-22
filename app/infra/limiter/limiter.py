from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.infra.common.errors import error_detail
from app.infra.config import settings
from app.infra.limiter.constants import RATE_LIMIT, RATE_LIMIT_EXCEEDED_CODE, RATE_LIMIT_EXCEEDED_MESSAGE

# Applies to every route automatically, keyed by client IP.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT],
    enabled=settings.rate_limit_enabled,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    detail = error_detail(RATE_LIMIT_EXCEEDED_CODE, RATE_LIMIT_EXCEEDED_MESSAGE.format(detail=exc.detail))
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": detail})
