"""API integration tests for GET/PATCH /api/users/me."""

import pytest


class TestUsersMeAPI:
    """Tests for the /me self-service endpoints."""

    @pytest.mark.asyncio
    async def test_get_me_returns_200(
        self,
        client_users,
        test_instructor,
        routes,
    ):
        """GET /me returns current user."""
        response = await client_users.get(routes.users_me)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_instructor.id)
        assert data["email"] == test_instructor.email
        assert data["role"] == test_instructor.role.value
        assert data["is_active"] is True
        assert data["is_verified"] is True

    @pytest.mark.asyncio
    async def test_patch_me_updates_password_returns_200(
        self,
        client_users,
        test_instructor,
        routes,
    ):
        """PATCH /me with password returns 200."""
        payload = {"password": "NewPass1!"}

        response = await client_users.patch(routes.users_update_me, json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_instructor.id)
        assert data["email"] == test_instructor.email
