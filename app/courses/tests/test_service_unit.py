"""Unit tests for courses service (pure functions, no DB)."""

import uuid

import pytest

from app.courses.schemas import CourseCreate
from app.courses.service import _resolve_instructor_ids


class TestResolveInstructorIds:
    """Tests for _resolve_instructor_ids."""

    @pytest.mark.parametrize(
        "add_me,instructor_ids,expected",
        [
            (True, [], "current_only"),
            (False, "single_other", "other_only"),
            (True, "single_other", "current_then_other"),
            (True, "creator", "current_only"),
            (False, "duplicates", "other_then_current"),
        ],
        ids=["add_me_only", "add_me_false", "creator_first", "dedupe_creator", "dedupe_ids"],
    )
    def test_resolve_instructor_ids(self, add_me, instructor_ids, expected):
        """Resolved instructor IDs match expected order and deduplication."""
        current = uuid.uuid4()
        other = uuid.uuid4()

        if instructor_ids == "single_other":
            ids = [other]
        elif instructor_ids == "creator":
            ids = [current]
        elif instructor_ids == "duplicates":
            ids = [other, other, current, other]
        else:
            ids = instructor_ids

        payload = CourseCreate(
            title="Course",
            add_me_as_instructor=add_me,
            instructor_ids=ids,
        )
        result = _resolve_instructor_ids(payload, current)

        if expected == "current_only":
            assert result == [current]
        elif expected == "other_only":
            assert result == [other]
        elif expected == "current_then_other":
            assert result == [current, other]
        elif expected == "other_then_current":
            assert result == [other, current]
