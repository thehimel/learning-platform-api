"""Shared fixtures for the courses test suite."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.repository import CourseRepository


@pytest.fixture
def course_repository(db_session: AsyncSession) -> CourseRepository:
    """Repository bound to the test's transactional session, for exercising the service layer directly."""
    return CourseRepository(db_session)
