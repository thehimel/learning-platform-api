"""API integration tests for PATCH /api/courses/{id}."""

import uuid

import pytest


class TestUpdateCourseAPI:
    """Tests for the update course endpoint (PATCH /courses/{id})."""

    @pytest.mark.asyncio
    async def test_update_course_title_returns_200(self, client, routes):
        """Instructor can update course title."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Original", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.patch(
            routes.courses_update(course_id),
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_course_description(self, client, routes):
        """Instructor can update course description."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Course", "description": "Old", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.patch(
            routes.courses_update(course_id),
            json={"description": "New description"},
        )

        assert response.status_code == 200
        assert response.json()["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_course_published(self, client, routes):
        """Instructor can publish a course."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Draft Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]
        assert create_resp.json()["published"] is False

        response = await client.patch(
            routes.courses_update(course_id),
            json={"published": True},
        )

        assert response.status_code == 200
        assert response.json()["published"] is True

    @pytest.mark.asyncio
    async def test_update_course_instructor_ids(self, client, test_instructor, routes):
        """Instructor can update course instructors."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.patch(
            routes.courses_update(course_id),
            json={"instructor_ids": [str(test_instructor.id)]},
        )

        assert response.status_code == 200
        assert len(response.json()["instructors"]) == 1
        assert response.json()["instructors"][0]["id"] == str(test_instructor.id)

    @pytest.mark.asyncio
    async def test_update_course_nonexistent_returns_404(self, client, routes):
        """Updating non-existent course returns 404."""
        response = await client.patch(
            routes.courses_update(99999),
            json={"title": "Updated"},
        )

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "course_not_found"

    @pytest.mark.asyncio
    async def test_update_course_invalid_instructor_ids_returns_400(self, client, test_instructor, routes):
        """Invalid instructor_ids returns 400."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.patch(
            routes.courses_update(course_id),
            json={"instructor_ids": [str(uuid.uuid4())]},
        )

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "invalid_instructor_ids"

    @pytest.mark.asyncio
    async def test_update_course_empty_instructor_ids_returns_400(self, client, test_instructor, routes):
        """Empty instructor_ids returns 400 with cannot_remove_last_instructor."""
        create_resp = await client.post(
            routes.courses_create,
            json={"title": "Course", "add_me_as_instructor": True, "instructor_ids": []},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client.patch(
            routes.courses_update(course_id),
            json={"instructor_ids": []},
        )

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "cannot_remove_last_instructor"

    @pytest.mark.asyncio
    async def test_update_course_not_instructor_returns_403(
        self, client_e2e, instructor_e2e, other_instructor_e2e, routes
    ):
        """Instructor who is not instructor of course cannot update it."""
        _, instructor_token = instructor_e2e
        _, other_token = other_instructor_e2e

        create_resp = await client_e2e.post(
            routes.courses_create,
            json={"title": "Instructor Course", "add_me_as_instructor": True, "instructor_ids": []},
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client_e2e.patch(
            routes.courses_update(course_id),
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "not_instructor_of_course"

    @pytest.mark.asyncio
    async def test_admin_can_update_any_course(self, client_e2e, instructor_e2e, admin_e2e, routes):
        """Admin can update a course they are not instructor of."""
        _, instructor_token = instructor_e2e
        _, admin_token = admin_e2e

        create_resp = await client_e2e.post(
            routes.courses_create,
            json={"title": "Instructor Course", "add_me_as_instructor": True, "instructor_ids": []},
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        response = await client_e2e.patch(
            routes.courses_update(course_id),
            json={"title": "Admin Updated"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Admin Updated"
