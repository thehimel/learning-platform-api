from fastapi import APIRouter

from app.auth.backend import auth_backend, fastapi_users
from app.auth.constants import AUTH_TAG, JWT_PREFIX
from app.users.schemas import UserCreate, UserRead

router = APIRouter()

# Adds POST /jwt/login (token) and POST /jwt/logout (client-side invalidate).
router.include_router(fastapi_users.get_auth_router(auth_backend), prefix=JWT_PREFIX, tags=[AUTH_TAG])

router.include_router(fastapi_users.get_register_router(UserRead, UserCreate), tags=[AUTH_TAG])
