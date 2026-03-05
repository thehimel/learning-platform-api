"""Unit tests for update_course service."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.errors import CannotRemoveLastInstructorError, TooManyInstructorsError
from app.courses.schemas import CourseCreate, CourseUpdate, MAX_INSTRUCTORS_PER_COURSE
from app.courses.service import create_course, update_course
from app.users.models import User


class TestUpdateCourseServiceExceptions:
    """Tests for update_course exception cases."""

    @pytest.mark.asyncio
    async def test_update_course_too_many_instructors_raises(
        self,
        db_session: AsyncSession,
        test_instructor: User,
    ):
        """Too many instructor_ids raises TooManyInstructorsError."""
        create_resp = await create_course(
            CourseCreate(title="Course", add_me_as_instructor=True, instructor_ids=[]),
            test_instructor,
            db_session,
        )
        course_id = create_resp.id

        payload = CourseUpdate.model_construct(
            instructor_ids=[uuid.uuid4() for _ in range(MAX_INSTRUCTORS_PER_COURSE + 1)],
        )

        with pytest.raises(TooManyInstructorsError):
            await update_course(course_id, payload, test_instructor, db_session)

    @pytest.mark.asyncio
    async def test_update_course_empty_instructor_ids_raises(
        self,
        db_session: AsyncSession,
        test_instructor: User,
    ):
        """Empty instructor_ids raises CannotRemoveLastInstructorError."""
        create_resp = await create_course(
            CourseCreate(title="Course", add_me_as_instructor=True, instructor_ids=[]),
            test_instructor,
            db_session,
        )
        course_id = create_resp.id

        payload = CourseUpdate.model_construct(instructor_ids=[])

        with pytest.raises(CannotRemoveLastInstructorError):
            await update_course(course_id, payload, test_instructor, db_session)
