import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_short_link(async_client: AsyncClient):
    await async_client.post("/auth/register", json={
        "email": "linktest@example.com",
        "password": "pass1234"
    })

    response = await async_client.post("/auth/login", data={
        "username": "linktest@example.com",
        "password": "pass1234"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post("/links/shorten", json={
        "original_url": "https://example.com/test123"
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com/test123"


@pytest.mark.asyncio
async def test_redirect_short_link(async_client: AsyncClient):
    await async_client.post("/auth/register", json={
        "email": "rediruser@example.com",
        "password": "pass1234"
    })

    response = await async_client.post("/auth/login", data={
        "username": "rediruser@example.com",
        "password": "pass1234"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    original_url = "https://example.com/redirect"
    response = await async_client.post("/links/shorten", json={
        "original_url": original_url
    }, headers=headers)
    short_code = response.json()["short_code"]

    response = await async_client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == original_url


@pytest.mark.asyncio
async def test_link_stats(async_client: AsyncClient):
    await async_client.post("/auth/register", json={
        "email": "statuser@example.com",
        "password": "statpass123"
    })

    response = await async_client.post("/auth/login", data={
        "username": "statuser@example.com",
        "password": "statpass123"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post("/links/shorten", json={
        "original_url": "https://example.com/stats"
    }, headers=headers)
    short_code = response.json()["short_code"]

    await async_client.get(f"/{short_code}")

    response = await async_client.get(f"/links/{short_code}/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://example.com/stats"
    assert data["click_count"] >= 1
    assert data["last_click"] is not None


@pytest.mark.asyncio
async def test_update_and_delete_link(async_client: AsyncClient):
    await async_client.post("/auth/register", json={
        "email": "updateuser@example.com",
        "password": "updatepass"
    })

    login_resp = await async_client.post("/auth/login", data={
        "username": "updateuser@example.com",
        "password": "updatepass"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post("/links/shorten", json={
        "original_url": "https://update.com"
    }, headers=headers)
    short_code = create_resp.json()["short_code"]

    new_url = "https://updated-url.com"
    update_resp = await async_client.put(f"/links/{short_code}", json={
        "original_url": new_url
    }, headers=headers)

    assert update_resp.status_code == 200
    assert update_resp.json()["original_url"].rstrip("/") == new_url.rstrip("/")

    delete_resp = await async_client.delete(f"/links/{short_code}", headers=headers)
    assert delete_resp.status_code == 204