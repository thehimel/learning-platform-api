"""Constants for the auth module: JWT backend wiring and fastapi-users route names."""

from enum import StrEnum

JWT_BACKEND_NAME = "jwt"
JWT_PREFIX = "/jwt"
SECONDS_PER_MINUTE = 60

AUTH_TAG = "Auth"

# Must match the mounted path: API prefix, then auth prefix, then JWT prefix.
TOKEN_URL = "api/auth/jwt/login"


class RouteName(StrEnum):
    """FastAPI Users route names."""

    auth_login = "auth:jwt.login"
    auth_register = "register:register"
