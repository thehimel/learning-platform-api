import uuid
from typing import Optional

from pydantic import ConfigDict, model_validator
from fastapi_users import schemas

from app.users.constants import IS_SUPERUSER_FIELD, PRIVILEGED_FIELDS, PRIVILEGED_UPDATE_FIELDS
from app.users.models import UserRole


def _make_schema_cleaner(*fields: str):
    """Return a json_schema_extra callback that removes the given fields."""

    def cleaner(schema: dict) -> None:
        for field in fields:
            schema.get("properties", {}).pop(field, None)
            if field in schema.get("required", []):
                schema["required"].remove(field)

    return cleaner


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: UserRole


class UserCreate(schemas.BaseUserCreate):
    """Only email and password are accepted on registration. is_active, is_superuser, is_verified are stripped from the
    request and hidden from the OpenAPI schema — their values are always set server-side via database defaults.
    """

    model_config = ConfigDict(json_schema_extra=_make_schema_cleaner(*PRIVILEGED_FIELDS))

    @model_validator(mode="before")
    @classmethod
    def enforce_safe_defaults(cls, values: object) -> object:
        # mode="before" may receive bytes or a model instance, not only a dict.
        if isinstance(values, dict):
            for field in PRIVILEGED_FIELDS:
                values.pop(field, None)
        return values


class UserUpdate(schemas.BaseUserUpdate):
    """Only password is accepted on self-update (PATCH /api/users/me). role and email changes are handled via a
    dedicated admin endpoint. is_active, is_superuser, is_verified are always managed server-side. Email is blocked
    until email verification is enabled (see docs/config/auth/email-setup.md).
    """

    model_config = ConfigDict(json_schema_extra=_make_schema_cleaner(*PRIVILEGED_UPDATE_FIELDS))

    @model_validator(mode="before")
    @classmethod
    def enforce_safe_defaults(cls, values: object) -> object:
        # mode="before" may receive bytes or a model instance, not only a dict.
        if isinstance(values, dict):
            for field in PRIVILEGED_UPDATE_FIELDS:
                values.pop(field, None)
        return values


class UserAdminUpdate(schemas.BaseUserUpdate):
    """All fields editable — used exclusively on PATCH /api/users/{id} (admin only).
    BaseUserUpdate provides: password, email, is_active, is_verified.

    is_superuser is excluded — it no longer exists as a DB column and is derived
    from role via a hybrid_property on the User model.
    """

    model_config = ConfigDict(json_schema_extra=_make_schema_cleaner(IS_SUPERUSER_FIELD))

    role: Optional[UserRole] = None
    is_superuser: None = None  # type: ignore[assignment]
