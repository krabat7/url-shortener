import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello! Welcome to the app - URL Shortener API!"}


@pytest.mark.asyncio
async def test_redirect_invalid_code(async_client: AsyncClient):
    response = await async_client.get("/nonexistentcode")
    assert response.status_code == 404
    assert response.json()["detail"] == "Short link not found"


@pytest.mark.asyncio
async def test_redirect_expired_link(async_client: AsyncClient):
    await async_client.post("/auth/register", json={
        "email": "expiredcase@example.com",
        "password": "expired123"
    })
    login_resp = await async_client.post("/auth/login", data={
        "username": "expiredcase@example.com",
        "password": "expired123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    expired_at = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    resp = await async_client.post("/links/shorten", json={
        "original_url": "https://expired.link",
        "expires_at": expired_at
    }, headers=headers)
    short_code = resp.json()["short_code"]

    resp = await async_client.get(f"/{short_code}")
    assert resp.status_code == 410
    assert resp.json()["detail"] == "Link has expired"


@pytest.mark.asyncio
async def test_redirect_with_redis_hit(async_client: AsyncClient, monkeypatch):
    class FakeRedis:
        async def get(self, key): return "https://redis-test.com"
        async def setex(self, *args, **kwargs): pass
        async def delete(self, *args, **kwargs): pass

    async def fake_get_redis():
        return FakeRedis()

    monkeypatch.setattr("app.api.main.get_redis", fake_get_redis)

    await async_client.post("/auth/register", json={
        "email": "cache@example.com",
        "password": "secure123"
    })
    login = await async_client.post("/auth/login", data={
        "username": "cache@example.com",
        "password": "secure123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await async_client.post("/links/shorten", json={
        "original_url": "https://somewhere.com"
    }, headers=headers)
    short_code = resp.json()["short_code"]

    resp = await async_client.get(f"/{short_code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"].rstrip("/") == "https://redis-test.com"


def test_app_instance():
    assert app.title == "URL Shortener"