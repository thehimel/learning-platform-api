from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import router as api_router
from app.health.router import router as health_router
from app.index.router import router as index_router
from app.infra.common.constants import API_PREFIX, CORS_ALLOW_ALL, CORS_ORIGIN_SEPARATOR
from app.infra.common.exception_handler import register_exception_handlers
from app.infra.common.setup_request_logging import setup_request_logging
from app.infra.common.setup_security import setup_security_headers
from app.infra.config import settings
from app.infra.limiter import limiter, rate_limit_exceeded_handler
from app.infra.logging import configure_logging
from app.users.errors import register_user_exception_handlers

configure_logging()

app = FastAPI()

app.state.limiter = limiter  # type: ignore[attr-defined]
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

register_exception_handlers(app)
register_user_exception_handlers(app)
app.add_middleware(SlowAPIMiddleware)

origins = (
    [o.strip() for o in settings.cors_origins.split(CORS_ORIGIN_SEPARATOR) if o.strip()]
    if settings.cors_origins != CORS_ALLOW_ALL
    else [CORS_ALLOW_ALL]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[CORS_ALLOW_ALL],
    allow_headers=[CORS_ALLOW_ALL],
)
setup_security_headers(app)
app.add_middleware(GZipMiddleware)
setup_request_logging(app)

app.include_router(api_router, prefix=API_PREFIX)
app.include_router(index_router)
app.include_router(health_router, prefix="/health")
