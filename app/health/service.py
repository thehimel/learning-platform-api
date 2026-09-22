from sqlalchemy import text

from app.health.constants import HEALTH_CHECK_QUERY
from app.infra.database import engine


async def check_db() -> None:
    """Verify DB connectivity for load balancers / k8s readiness probes."""
    async with engine.connect() as conn:
        await conn.execute(text(HEALTH_CHECK_QUERY))
