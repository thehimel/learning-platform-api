"""API integration tests for GET /api/courses/."""

import pytest


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
