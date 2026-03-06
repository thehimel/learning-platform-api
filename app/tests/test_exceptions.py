"""Unit tests for app.exceptions."""

import pytest

from app.courses.error_codes import CourseErrorCode
from app.exceptions import error_detail
from app.users.error_codes import UserErrorCode


class TestErrorDetail:
    """Tests for error_detail helper."""

    def test_returns_code_and_message(self):
        """Basic structure with code and message."""
        result = error_detail(UserErrorCode.user_not_found, "User not found.")
        assert result == {"code": "user_not_found", "message": "User not found."}

    @pytest.mark.parametrize(
        "code,message,extra,expected_keys",
        [
            (
                CourseErrorCode.invalid_instructor_ids,
                "Invalid instructors.",
                {"missing_ids": ["id1", "id2"]},
                ["code", "message", "missing_ids"],
            ),
            (
                CourseErrorCode.invalid_instructor_ids,
                "Invalid.",
                {"missing_ids": ["a"], "count": 2},
                ["code", "message", "missing_ids", "count"],
            ),
        ],
        ids=["single_extra", "multiple_extra"],
    )
    def test_includes_extra_kwargs(self, code, message, extra, expected_keys):
        """Extra kwargs are merged into the dict."""
        result = error_detail(code, message, **extra)
        for key in expected_keys:
            assert key in result
        assert result["code"] == code.value
        assert result["message"] == message
        assert result.get("missing_ids") == extra.get("missing_ids")
        if "count" in extra:
            assert result["count"] == extra["count"]
