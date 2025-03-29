import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_search_and_expired_and_cleanup(async_client):
    await async_client.post("/auth/register", json={
        "email": "searchuser@example.com",
        "password": "searchpass"
    })
    login_resp = await async_client.post("/auth/login", data={
        "username": "searchuser@example.com",
        "password": "searchpass"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    expired_time = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    await async_client.post("/links/shorten", json={
        "original_url": "https://expired.com",
        "expires_at": expired_time
    }, headers=headers)

    await async_client.post("/links/shorten", json={
        "original_url": "https://cleanup.com"
    }, headers=headers)

    expired_resp = await async_client.get("/links/expired", headers=headers)
    assert expired_resp.status_code == 200
    assert any("expired.com" in l["original_url"] for l in expired_resp.json())

    created_url = f"https://cleanup.com/{datetime.utcnow().timestamp()}"
    await async_client.post("/links/shorten", json={
        "original_url": created_url
    }, headers=headers)

    search_resp = await async_client.get("/links/search", params={"original_url": created_url}, headers=headers)
    assert search_resp.status_code == 200
    assert search_resp.json()["original_url"] == created_url


@pytest.mark.asyncio
async def test_search_success(async_client):
    await async_client.post("/auth/register", json={
        "email": "searchok@example.com",
        "password": "secure123"
    })
    login = await async_client.post("/auth/login", data={
        "username": "searchok@example.com",
        "password": "secure123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = await async_client.post("/links/shorten", json={
        "original_url": "https://search-this.com"
    }, headers=headers)
    created_url = create.json()["original_url"]

    search = await async_client.get("/links/search", params={"original_url": created_url}, headers=headers)
    assert search.status_code == 200
    assert search.json()["original_url"] == created_url


@pytest.mark.asyncio
async def test_search_not_found(async_client):
    await async_client.post("/auth/register", json={
        "email": "search404@example.com",
        "password": "secure123"
    })
    login = await async_client.post("/auth/login", data={
        "username": "search404@example.com",
        "password": "secure123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/links/search", params={
        "original_url": "https://notfound.com"
    }, headers=headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_without_auth(async_client):
    resp = await async_client.get("/links/search", params={
        "original_url": "https://noauth.com"
    })
    assert resp.status_code == 401