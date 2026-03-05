"""API integration tests for DELETE /api/courses/{id}."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.schemas import CourseCreate
from app.courses.service import create_course as create_course_service

_CREATE_PAYLOAD = {"title": "To Delete", "add_me_as_instructor": True, "instructor_ids": []}


class TestDeleteCourseAPI:
    """Tests for the delete course endpoint (DELETE /courses/{id})."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "delete_client,create_via",
        [
            ("client", "api"),
            ("client_admin", "service"),
        ],
        ids=["instructor_deletes_own", "admin_deletes_any"],
    )
    async def test_delete_success(
        self,
        delete_client,
        create_via,
        client,
        client_admin,
        db_session: AsyncSession,
        test_admin,
        routes,
    ):
        """Instructor or admin can delete; course is removed."""
        http_client = client_admin if delete_client == "client_admin" else client

        if create_via == "api":
            create_resp = await client.post(routes.courses_create, json=_CREATE_PAYLOAD)
            assert create_resp.status_code == 201
            course_id = create_resp.json()["id"]
        else:
            payload = CourseCreate(**_CREATE_PAYLOAD, published=False)
            course = await create_course_service(payload, test_admin, db_session)
            await db_session.commit()
            course_id = course.id

        delete_resp = await http_client.delete(routes.courses_delete(course_id))
        assert delete_resp.status_code == 204

        get_resp = await client.get(routes.courses_get_by_id(course_id))
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "setup,expected_status,expected_code",
        [
            ("nonexistent", 404, "course_not_found"),
            ("other_instructor", 403, "not_instructor_of_course"),
        ],
        ids=["nonexistent_404", "instructor_cannot_delete_other"],
    )
    async def test_delete_errors(
        self,
        setup,
        expected_status,
        expected_code,
        client,
        db_session: AsyncSession,
        test_admin,
        routes,
    ):
        """Delete returns expected error for unauthorized or nonexistent."""
        if setup == "nonexistent":
            course_id = 99999
        else:
            payload = CourseCreate(**_CREATE_PAYLOAD, published=False)
            course = await create_course_service(payload, test_admin, db_session)
            await db_session.commit()
            course_id = course.id

        delete_resp = await client.delete(routes.courses_delete(course_id))
        assert delete_resp.status_code == expected_status
        assert delete_resp.json()["detail"]["code"] == expected_code
