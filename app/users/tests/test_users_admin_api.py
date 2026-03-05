"""API integration tests for GET/PATCH/DELETE /api/users/{id} (admin)."""

import uuid

import pytest


class TestUsersAdminAPI:
    """Tests for the admin user management endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_returns_200(
        self,
        client_admin,
        test_instructor,
        routes,
    ):
        """Admin GET /{id} returns user when exists."""
        response = await client_admin.get(routes.users_by_id(test_instructor.id))

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_instructor.id)
        assert data["email"] == test_instructor.email
        assert data["role"] == test_instructor.role.value

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["get", "patch", "delete"], ids=["get", "patch", "delete"])
    async def test_user_not_found_returns_404(self, client_admin, routes, method):
        """Admin GET/PATCH/DELETE /{id} returns 404 when user does not exist."""
        url = routes.users_by_id(uuid.uuid4())
        if method == "get":
            response = await client_admin.get(url)
        elif method == "patch":
            response = await client_admin.patch(url, json={"role": "instructor"})
        else:
            response = await client_admin.delete(url)

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "user_not_found"
        assert "message" in data["detail"]

    @pytest.mark.asyncio
    async def test_patch_user_returns_200(
        self,
        client_admin,
        test_instructor,
        routes,
    ):
        """Admin PATCH /{id} updates user."""
        payload = {"role": "instructor"}

        response = await client_admin.patch(routes.users_by_id(test_instructor.id), json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "instructor"

    @pytest.mark.asyncio
    async def test_delete_user_returns_204(
        self,
        client_admin,
        test_instructor,
        routes,
    ):
        """Admin DELETE /{id} returns 204 when user exists and is not self."""
        response = await client_admin.delete(routes.users_by_id(test_instructor.id))

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_self_returns_403(
        self,
        client_admin,
        test_admin,
        routes,
    ):
        """Admin DELETE /{id} returns 403 when deleting own account."""
        response = await client_admin.delete(routes.users_by_id(test_admin.id))

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "cannot_delete_self"
