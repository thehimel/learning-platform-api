from fastapi import APIRouter

from app.health.constants import HEALTH_OK_STATUS, RouteName
from app.health.service import check_db
from app.infra.limiter import limiter

router = APIRouter()


@router.get("/db", name=RouteName.health_db)
@limiter.exempt
async def health_db():
    await check_db()
    return {"status": HEALTH_OK_STATUS}
