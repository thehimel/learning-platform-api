from fastapi import APIRouter

from app.api.constants import AUTH_PREFIX, AUTH_TAG, COURSES_PREFIX, COURSES_TAG, USERS_PREFIX, USERS_TAG
from app.auth.router import router as auth_router
from app.courses.router import router as courses_router
from app.users.router import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix=AUTH_PREFIX, tags=[AUTH_TAG])
router.include_router(users_router, prefix=USERS_PREFIX, tags=[USERS_TAG])
router.include_router(courses_router, prefix=COURSES_PREFIX, tags=[COURSES_TAG])
