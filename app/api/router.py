from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.courses.router import router as courses_router
from app.users.router import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(courses_router, prefix="/courses", tags=["Courses"])
