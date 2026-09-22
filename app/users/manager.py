import uuid
from typing import Optional

from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import InvalidPasswordException
from password_strength import PasswordPolicy

from app.infra.config import settings
from app.infra.logging import get_logger
from app.users.constants import (
    PASSWORD_CONTAINS_EMAIL_MESSAGE,
    PASSWORD_MIN_LENGTH,
    PASSWORD_MIN_NONLETTERS,
    PASSWORD_MIN_NUMBERS,
    PASSWORD_MIN_SPECIAL,
    PASSWORD_MIN_UPPERCASE,
    PASSWORD_POLICY_MESSAGES,
    PASSWORD_RESET_EVENT,
    PASSWORD_RESET_REQUESTED_EVENT,
    PRIVILEGE_CHANGE_EVENT,
    ROLE_UPDATE_FIELD,
    USER_DELETED_EVENT,
    USER_DELETE_STARTED_EVENT,
    USER_LOGGED_IN_EVENT,
    USER_REGISTERED_EVENT,
)
from app.users.dependencies import get_user_db
from app.users.models import User

logger = get_logger(__name__)

_password_policy = PasswordPolicy.from_names(
    length=PASSWORD_MIN_LENGTH,
    uppercase=PASSWORD_MIN_UPPERCASE,
    numbers=PASSWORD_MIN_NUMBERS,
    special=PASSWORD_MIN_SPECIAL,
    nonletters=PASSWORD_MIN_NONLETTERS,
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.auth_reset_password_token_secret
    verification_token_secret = settings.auth_verification_token_secret

    async def validate_password(self, password: str, user) -> None:
        failures = _password_policy.test(password)
        if failures:
            reasons = "; ".join(PASSWORD_POLICY_MESSAGES.get(type(f).__name__, str(f)) for f in failures)
            raise InvalidPasswordException(reason=reasons)

        if hasattr(user, "email") and user.email and user.email.split("@")[0].lower() in password.lower():
            raise InvalidPasswordException(reason=PASSWORD_CONTAINS_EMAIL_MESSAGE)

    async def on_after_update(self, user: User, update_dict: dict, request: Optional[Request] = None):
        if ROLE_UPDATE_FIELD in update_dict:
            logger.warning(PRIVILEGE_CHANGE_EVENT, user_id=user.id, role=user.role)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(USER_REGISTERED_EVENT, user_id=user.id, role=user.role)

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ):
        logger.info(USER_LOGGED_IN_EVENT, user_id=user.id)

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        logger.info(PASSWORD_RESET_REQUESTED_EVENT, user_id=user.id)
        # TODO: send password reset email.

    async def on_after_reset_password(self, user: User, request: Optional[Request] = None):
        logger.info(PASSWORD_RESET_EVENT, user_id=user.id)

    async def on_before_delete(self, user: User, request: Optional[Request] = None):
        logger.info(USER_DELETE_STARTED_EVENT, user_id=user.id)

    async def on_after_delete(self, user: User, request: Optional[Request] = None):
        logger.info(USER_DELETED_EVENT, user_id=user.id)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)
