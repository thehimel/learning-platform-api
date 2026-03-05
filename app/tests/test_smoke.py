"""Smoke tests — minimal checks that the app starts and basic paths respond."""

import pytest
import httpx

from app.main import app

TEST_CLIENT_BASE_URL = "http://test.server"


@pytest.fixture
async def smoke_client():
    """Minimal HTTP client for smoke tests (no dependency overrides)."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=TEST_CLIENT_BASE_URL,
    ) as client:
        yield client


class TestSmoke:
    """Smoke tests for app startup and basic endpoints."""

    @pytest.mark.asyncio
    async def test_root_returns_200(self, smoke_client):
        """GET / returns 200 with message."""
        response = await smoke_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello World"

    @pytest.mark.asyncio
    async def test_health_db_returns_200(self, smoke_client):
        """GET /health/db returns 200 when DB is reachable."""
        response = await smoke_client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
