import uuid
from typing import Optional

from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import InvalidPasswordException
from password_strength import PasswordPolicy

from app.config import settings
from app.logger import get_logger
from app.users.dependencies import get_user_db
from app.users.models import User

logger = get_logger(__name__)

_password_policy = PasswordPolicy.from_names(
    length=8,  # minimum 8 characters
    uppercase=1,  # at least 1 uppercase letter
    numbers=1,  # at least 1 digit
    special=1,  # at least 1 special character
    nonletters=1,  # at least 1 non-letter (digit or special)
)

# Human-readable names for each failed test, keyed on the class name returned by password-strength.
_POLICY_MESSAGES: dict[str, str] = {
    "Length": "Password must be at least 8 characters.",
    "Uppercase": "Password must contain at least 1 uppercase letter.",
    "Numbers": "Password must contain at least 1 digit.",
    "Special": "Password must contain at least 1 special character.",
    "NonLetters": "Password must contain at least 1 non-letter character.",
}


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.auth_reset_password_token_secret
    verification_token_secret = settings.auth_verification_token_secret

    async def validate_password(self, password: str, user) -> None:
        failures = _password_policy.test(password)
        if failures:
            reasons = "; ".join(_POLICY_MESSAGES.get(type(f).__name__, str(f)) for f in failures)
            raise InvalidPasswordException(reason=reasons)

        if hasattr(user, "email") and user.email and user.email.split("@")[0].lower() in password.lower():
            raise InvalidPasswordException(reason="Password must not contain your email address.")

    async def on_after_update(self, user: User, update_dict: dict, request: Optional[Request] = None):
        if "role" in update_dict:
            logger.warning("Privilege change: user %s role set to '%s'.", user.id, user.role)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info("User %s registered with role '%s'.", user.id, user.role)

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ):
        logger.info("User %s logged in.", user.id)

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        logger.info("User %s requested a password reset.", user.id)
        # TODO: send password reset email — see docs/config/email-setup.md

    async def on_after_reset_password(self, user: User, request: Optional[Request] = None):
        logger.info("User %s reset their password.", user.id)

    async def on_before_delete(self, user: User, request: Optional[Request] = None):
        logger.info("User %s is about to be deleted.", user.id)

    async def on_after_delete(self, user: User, request: Optional[Request] = None):
        logger.info("User %s has been deleted.", user.id)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)
