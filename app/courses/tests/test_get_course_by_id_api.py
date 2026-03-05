"""API integration tests for GET /api/courses/{id}."""

import pytest


class TestGetCourseByIdAPI:
    """Tests for the get course by ID endpoint (GET /courses/{id})."""

    @pytest.mark.asyncio
    async def test_get_course_returns_200_with_full_details(
        self,
        client,
        test_instructor,
        routes,
    ):
        """GET /courses/{id} returns 200 with instructors, rating, enrolled_count."""
        create_resp = await client.post(
            routes.courses_create,
            json={
                "title": "Python Basics",
                "description": "Learn Python",
                "add_me_as_instructor": True,
                "instructor_ids": [],
            },
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.get(routes.courses_get_by_id(course_id))

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == course_id
        assert data["title"] == "Python Basics"
        assert data["description"] == "Learn Python"
        assert data["published"] is False
        assert data["rating"] is None
        assert data["enrolled_count"] == 0
        assert len(data["instructors"]) == 1
        assert data["instructors"][0]["id"] == str(test_instructor.id)
        assert data["instructors"][0]["email"] == test_instructor.email
        assert data["instructors"][0]["is_primary"] is True
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_course_with_enrollments_shows_count(self, client, routes):
        """GET /courses/{id} includes enrolled_count after enrollments."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Enrolled Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        await client.post(routes.courses_enroll(course_id))
        response = await client.get(routes.courses_get_by_id(course_id))

        assert response.status_code == 200
        assert response.json()["enrolled_count"] == 1

    @pytest.mark.asyncio
    async def test_get_course_with_rating_shows_rating(self, client, routes):
        """GET /courses/{id} includes rating after user rates."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Rated Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        await client.post(routes.courses_rate(course_id), json={"rating": 4.5})
        response = await client.get(routes.courses_get_by_id(course_id))

        assert response.status_code == 200
        assert response.json()["rating"] == 4.5

    @pytest.mark.asyncio
    async def test_get_course_nonexistent_returns_404(self, client, routes):
        """GET /courses/{id} returns 404 when course does not exist."""
        response = await client.get(routes.courses_get_by_id(99999))

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "course_not_found"

    @pytest.mark.asyncio
    async def test_get_course_public_no_auth_required(self, client_e2e, instructor_e2e, routes):
        """GET /courses/{id} is public for published courses — no authentication required."""
        _, instructor_token = instructor_e2e
        create_resp = await client_e2e.post(
            routes.courses_create,
            json={"title": "Public Course", "add_me_as_instructor": True, "instructor_ids": [], "published": True},
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client_e2e.get(routes.courses_get_by_id(course_id))

        assert response.status_code == 200
        assert response.json()["title"] == "Public Course"

    @pytest.mark.asyncio
    async def test_get_course_unpublished_returns_404_without_auth(self, client_e2e, instructor_e2e, routes):
        """Unpublished courses return 404 for unauthenticated requests (IDOR prevention)."""
        _, instructor_token = instructor_e2e
        create_resp = await client_e2e.post(
            routes.courses_create,
            json={"title": "Draft Course", "add_me_as_instructor": True, "instructor_ids": []},
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client_e2e.get(routes.courses_get_by_id(course_id))

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "course_not_found"

    @pytest.mark.asyncio
    async def test_get_course_unpublished_returns_200_for_instructor(self, client, routes):
        """Instructors can access their own unpublished courses."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Draft Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.get(routes.courses_get_by_id(course_id))

        assert response.status_code == 200
        assert response.json()["title"] == "Draft Course"
        assert response.json()["published"] is False
