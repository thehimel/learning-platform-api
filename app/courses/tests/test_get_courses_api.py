"""API integration tests for GET /api/courses/."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.schemas import CourseCreate
from app.courses.service import create_course as create_course_service


class TestGetCoursesVisibility:
    """Tests for role-based visibility of courses (published vs unpublished)."""

    @pytest.mark.asyncio
    async def test_unauthenticated_sees_only_published(
        self,
        client,
        client_unauthenticated,
        routes,
    ):
        """Unauthenticated GET /courses returns only published courses."""
        # Create published and unpublished as instructor
        for title, published in [("Published", True), ("Unpublished", False)]:
            payload = {
                "title": title,
                "add_me_as_instructor": True,
                "instructor_ids": [],
                "published": published,
            }
            resp = await client.post(routes.courses_create, json=payload)
            assert resp.status_code == 201

        # Unauthenticated sees only published
        resp = await client_unauthenticated.get(routes.courses_get)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Published"

    @pytest.mark.asyncio
    async def test_instructor_sees_own_unpublished(
        self,
        client,
        test_instructor,
        routes,
    ):
        """Instructor GET /courses returns published + unpublished courses they instruct."""
        payload = {
            "title": "My Unpublished",
            "add_me_as_instructor": True,
            "instructor_ids": [],
            "published": False,
        }
        resp = await client.post(routes.courses_create, json=payload)
        assert resp.status_code == 201

        resp = await client.get(routes.courses_get)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "My Unpublished"
        assert data["items"][0]["published"] is False

    @pytest.mark.asyncio
    async def test_admin_sees_all_courses(
        self,
        client,
        client_admin,
        routes,
    ):
        """Admin GET /courses returns all courses including unpublished."""
        # Create published and unpublished as instructor
        for title, published in [("Published", True), ("Unpublished", False)]:
            payload = {
                "title": title,
                "add_me_as_instructor": True,
                "instructor_ids": [],
                "published": published,
            }
            resp = await client.post(routes.courses_create, json=payload)
            assert resp.status_code == 201

        # Admin sees all
        resp = await client_admin.get(routes.courses_get)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        titles = {c["title"] for c in data["items"]}
        assert titles == {"Published", "Unpublished"}

    @pytest.mark.asyncio
    async def test_instructor_does_not_see_other_instructor_unpublished(
        self,
        client,
        db_session: AsyncSession,
        test_admin,
        routes,
    ):
        """Instructor GET /courses does not return unpublished courses they do not instruct."""
        # Create unpublished course via service with admin as instructor (not test_instructor)
        payload = CourseCreate(
            title="Admin Unpublished",
            add_me_as_instructor=True,
            instructor_ids=[],
            published=False,
        )
        await create_course_service(payload, test_admin, db_session)
        await db_session.commit()

        # Instructor (test_instructor) does not see admin's unpublished course
        resp = await client.get(routes.courses_get)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0


class TestGetCoursesAPI:
    """Tests for the get courses endpoint (GET /courses)."""

    @pytest.mark.asyncio
    async def test_get_courses_empty_returns_200(self, client_e2e, routes):
        """GET /courses returns 200 with empty array when no courses exist (public endpoint)."""
        response = await client_e2e.get(routes.courses_get)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_courses_returns_created_courses(
        self,
        client,
        test_instructor,
        routes,
    ):
        """GET /courses returns courses created by instructor."""
        payload = {
            "title": "Course A",
            "description": "First course",
            "add_me_as_instructor": True,
            "instructor_ids": [],
            "published": True,
        }
        create_resp = await client.post(routes.courses_create, json=payload)
        assert create_resp.status_code == 201

        response = await client.get(routes.courses_get)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Course A"
        assert data["items"][0]["description"] == "First course"
        assert data["items"][0]["enrolled_count"] == 0
        assert len(data["items"][0]["instructors"]) == 1
        assert data["items"][0]["instructors"][0]["email"] == test_instructor.email

    @pytest.mark.asyncio
    async def test_get_courses_ordered_by_created_at_desc(
        self,
        client,
        routes,
    ):
        """GET /courses returns courses in reverse chronological order."""
        for title in ["First", "Second", "Third"]:
            payload = {
                "title": title,
                "add_me_as_instructor": True,
                "instructor_ids": [],
                "published": True,
            }
            await client.post(routes.courses_create, json=payload)

        response = await client.get(routes.courses_get)

        assert response.status_code == 200
        titles = [c["title"] for c in response.json()["items"]]
        assert titles == ["Third", "Second", "First"]

    @pytest.mark.asyncio
    async def test_get_courses_pagination(
        self,
        client,
        routes,
    ):
        """GET /courses respects limit and offset."""
        for i in range(5):
            payload = {
                "title": f"Course {i}",
                "add_me_as_instructor": True,
                "instructor_ids": [],
                "published": True,
            }
            await client.post(routes.courses_create, json=payload)

        # Default page
        resp = await client.get(routes.courses_get)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["total"] == 5
        assert data["limit"] == 20
        assert data["offset"] == 0

        # limit=2, offset=0
        resp2 = await client.get(f"{routes.courses_get}?limit=2&offset=0")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        assert data2["total"] == 5
        assert data2["limit"] == 2
        assert data2["offset"] == 0
        assert data2["items"][0]["title"] == "Course 4"
        assert data2["items"][1]["title"] == "Course 3"

        # limit=2, offset=2
        resp3 = await client.get(f"{routes.courses_get}?limit=2&offset=2")
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert len(data3["items"]) == 2
        assert data3["total"] == 5
        assert data3["items"][0]["title"] == "Course 2"
        assert data3["items"][1]["title"] == "Course 1"
