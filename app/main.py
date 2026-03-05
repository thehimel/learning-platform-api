from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.api.router import router as api_router
from app.auth.errors import register_auth_exception_handlers
from app.config import settings
from app.courses.errors import register_course_exception_handlers
from app.database import engine
from app.limiter import limiter, rate_limit_exceeded_handler
from app.users.errors import register_user_exception_handlers
from app.logger import configure_logging

configure_logging()

app = FastAPI()

app.state.limiter = limiter  # type: ignore[attr-defined]
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

register_auth_exception_handlers(app)
register_user_exception_handlers(app)
register_course_exception_handlers(app)
app.add_middleware(SlowAPIMiddleware)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


class RootResponse(BaseModel):
    message: str


@app.get("/", name="root", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(message="Hello World")


@app.get("/health/db", name="health_db")
async def health_db():
    """Verify DB connectivity for load balancers / k8s readiness probes."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
