"""Unit tests for users manager (password validation, no DB)."""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi_users.exceptions import InvalidPasswordException

from app.users.manager import UserManager
from app.users.models import User, UserRole


@pytest.fixture
def user_manager():
    """UserManager with mocked user_db."""
    return UserManager(user_db=MagicMock())


@pytest.fixture
def sample_user():
    """User with email for password validation tests."""
    return User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="john@example.com",
        hashed_password="",
        is_active=True,
        is_verified=True,
        role=UserRole.student,
    )


class TestValidatePassword:
    """Tests for UserManager.validate_password."""

    @pytest.mark.asyncio
    async def test_valid_password_passes(self, user_manager, sample_user):
        """Strong password passes validation."""
        await user_manager.validate_password("SecurePass1!", sample_user)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "password,reason_substring",
        [
            ("Short1!", "8 characters"),
            ("alllowercase1!", "uppercase"),
            ("NoDigitsHere!", "digit"),
            ("NoSpecial123", "special"),
            ("JohnPass1!", "email"),
            ("MyJohnPass1!", "email"),
        ],
        ids=["short", "no_uppercase", "no_digit", "no_special", "email_exact", "email_substring"],
    )
    async def test_invalid_password_raises(self, user_manager, sample_user, password, reason_substring):
        """Invalid password raises with expected reason."""
        with pytest.raises(InvalidPasswordException) as exc_info:
            await user_manager.validate_password(password, sample_user)
        assert reason_substring.lower() in exc_info.value.reason.lower()

    @pytest.mark.asyncio
    async def test_user_without_email_allows_any_valid_password(self, user_manager):
        """User without email skips email-in-password check."""
        user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            email=None,
            hashed_password="",
            is_active=True,
            is_verified=True,
            role=UserRole.student,
        )
        await user_manager.validate_password("SecurePass1!", user)
