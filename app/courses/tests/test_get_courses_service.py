"""Integration tests for get_courses service (service + DB)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.schemas import CourseCreate
from app.courses.service import create_course as create_course_service, get_courses
from app.users.models import User


class TestGetCoursesService:
    """Tests for get_courses service with real DB."""

    @pytest.mark.asyncio
    async def test_returns_published_only_for_unauthenticated(
        self,
        db_session: AsyncSession,
        test_instructor: User,
    ):
        """Unauthenticated user sees only published courses."""
        for title, published in [("Pub", True), ("Unpub", False)]:
            payload = CourseCreate(
                title=title,
                add_me_as_instructor=True,
                instructor_ids=[],
                published=published,
            )
            await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()

        courses, total = await get_courses(db_session, current_user=None)
        assert total == 1
        assert courses[0].title == "Pub"

    @pytest.mark.asyncio
    async def test_admin_sees_all_courses(
        self,
        db_session: AsyncSession,
        test_instructor: User,
        test_admin: User,
    ):
        """Admin sees all courses including unpublished."""
        for title, published in [("Pub", True), ("Unpub", False)]:
            payload = CourseCreate(
                title=title,
                add_me_as_instructor=True,
                instructor_ids=[],
                published=published,
            )
            await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()

        courses, total = await get_courses(db_session, current_user=test_admin)
        assert total == 2
        titles = {c.title for c in courses}
        assert titles == {"Pub", "Unpub"}

    @pytest.mark.asyncio
    async def test_instructor_sees_own_unpublished(
        self,
        db_session: AsyncSession,
        test_instructor: User,
    ):
        """Instructor sees published courses plus unpublished courses they instruct."""
        payload = CourseCreate(
            title="My Unpublished",
            add_me_as_instructor=True,
            instructor_ids=[],
            published=False,
        )
        await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()

        courses, total = await get_courses(db_session, current_user=test_instructor)
        assert total == 1
        assert courses[0].title == "My Unpublished"

    @pytest.mark.asyncio
    async def test_filter_by_published(
        self,
        db_session: AsyncSession,
        test_admin: User,
    ):
        """published filter restricts results."""
        for title, published in [("Pub", True), ("Unpub", False)]:
            payload = CourseCreate(
                title=title,
                add_me_as_instructor=True,
                instructor_ids=[],
                published=published,
            )
            await create_course_service(payload, test_admin, db_session)
        await db_session.commit()

        courses_pub, total_pub = await get_courses(db_session, current_user=test_admin, published=True)
        assert total_pub == 1
        assert courses_pub[0].title == "Pub"

        courses_unpub, total_unpub = await get_courses(db_session, current_user=test_admin, published=False)
        assert total_unpub == 1
        assert courses_unpub[0].title == "Unpub"

    @pytest.mark.asyncio
    async def test_filter_by_title_search(
        self,
        db_session: AsyncSession,
        test_instructor: User,
    ):
        """q filter does case-insensitive partial match on title."""
        for title in ["Python Basics", "Advanced Python", "JavaScript 101"]:
            payload = CourseCreate(
                title=title,
                add_me_as_instructor=True,
                instructor_ids=[],
                published=True,
            )
            await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()

        courses, total = await get_courses(db_session, current_user=None, q="python")
        assert total == 2
        titles = {c.title for c in courses}
        assert titles == {"Python Basics", "Advanced Python"}

        courses_js, total_js = await get_courses(db_session, current_user=None, q="JAVASCRIPT")
        assert total_js == 1
        assert courses_js[0].title == "JavaScript 101"

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        db_session: AsyncSession,
        test_instructor: User,
    ):
        """limit and offset work correctly."""
        for i in range(5):
            payload = CourseCreate(
                title=f"Course {i}",
                add_me_as_instructor=True,
                instructor_ids=[],
                published=True,
            )
            await create_course_service(payload, test_instructor, db_session)
        await db_session.commit()

        courses, total = await get_courses(db_session, current_user=None, limit=2, offset=1)
        assert total == 5
        assert len(courses) == 2
        assert courses[0].title == "Course 3"
        assert courses[1].title == "Course 2"
