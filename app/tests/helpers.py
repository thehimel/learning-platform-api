"""Shared helpers for E2E tests."""


async def e2e_login(client, email: str, password: str, login_path: str) -> str:
    """Login and return Bearer token."""
    response = await client.post(
        login_path,
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
