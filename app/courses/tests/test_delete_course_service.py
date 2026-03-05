"""Integration tests for delete_course service (service + DB)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.errors import CourseNotFoundError, NotInstructorOfCourseError
from app.courses.models import Course
from app.courses.schemas import CourseCreate
from app.courses.service import create_course as create_course_service, delete_course


class TestDeleteCourseService:
    """Tests for delete_course service with real DB."""

    @pytest.mark.asyncio
    async def test_admin_deletes_any_course(
        self,
        db_session: AsyncSession,
        test_admin,
        test_instructor,
    ):
        """Admin can delete a course they are not instructor of."""
        payload = CourseCreate(
            title="Admin Deletes",
            add_me_as_instructor=True,
            instructor_ids=[],
            published=False,
        )
        course = await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()
        course_id = course.id

        await delete_course(course_id, test_admin, db_session)

        result = await db_session.execute(select(Course).where(Course.id == course_id))
        assert result.scalars().one_or_none() is None

    @pytest.mark.asyncio
    async def test_instructor_deletes_own_course(
        self,
        db_session: AsyncSession,
        test_instructor,
    ):
        """Instructor can delete a course they instruct."""
        payload = CourseCreate(
            title="Instructor Deletes",
            add_me_as_instructor=True,
            instructor_ids=[],
            published=False,
        )
        course = await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()
        course_id = course.id

        await delete_course(course_id, test_instructor, db_session)

        result = await db_session.execute(select(Course).where(Course.id == course_id))
        assert result.scalars().one_or_none() is None

    @pytest.mark.asyncio
    async def test_instructor_cannot_delete_other_course(
        self,
        db_session: AsyncSession,
        test_admin,
        test_instructor,
    ):
        """Instructor cannot delete a course they do not instruct."""
        payload = CourseCreate(
            title="Other Course",
            add_me_as_instructor=True,
            instructor_ids=[],
            published=False,
        )
        course = await create_course_service(payload, test_admin, db_session)
        await db_session.commit()
        course_id = course.id

        with pytest.raises(NotInstructorOfCourseError):
            await delete_course(course_id, test_instructor, db_session)

        result = await db_session.execute(select(Course).where(Course.id == course_id))
        assert result.scalars().one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(
        self,
        db_session: AsyncSession,
        test_admin,
    ):
        """Deleting non-existent course raises CourseNotFoundError."""
        with pytest.raises(CourseNotFoundError):
            await delete_course(99999, test_admin, db_session)
