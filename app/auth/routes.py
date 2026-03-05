"""Route names for auth endpoints — from fastapi-users, used by url_path_for."""

from enum import StrEnum


class RouteName(StrEnum):
    """FastAPI Users route names."""

    auth_login = "auth:jwt.login"
    auth_register = "register:register"
