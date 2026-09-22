import uuid

from fastapi import Depends
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from app.auth.constants import JWT_BACKEND_NAME, SECONDS_PER_MINUTE, TOKEN_URL
from app.auth.errors import InsufficientPermissionsError
from app.infra.config import settings
from app.users.manager import get_user_manager
from app.users.models import User, UserRole

bearer_transport = BearerTransport(tokenUrl=TOKEN_URL)


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(
        secret=settings.jwt_secret_key,
        lifetime_seconds=settings.jwt_access_token_expire_minutes * SECONDS_PER_MINUTE,
        algorithm=settings.jwt_algorithm,
    )


auth_backend = AuthenticationBackend(
    name=JWT_BACKEND_NAME,
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)

# Returns None instead of raising when unauthenticated.
current_user_optional = fastapi_users.current_user(active=True, optional=True)


def require_role(*roles: UserRole):
    """Factory that returns a dependency enforcing one of the given roles."""

    async def checker(user: User = Depends(current_active_user)) -> User:
        if user.role not in roles:
            raise InsufficientPermissionsError()
        return user

    return checker


current_student = require_role(UserRole.student, UserRole.instructor, UserRole.admin)
current_instructor = require_role(UserRole.instructor, UserRole.admin)
current_admin = require_role(UserRole.admin)
