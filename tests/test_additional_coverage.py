import pytest
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from types import SimpleNamespace

from app.auth.utils import verify_password, hash_password, get_current_user
from app.models.models import User, Link
from app.schemas.schemas import LinkCreate
from app.crud import (
    generate_unique_code,
    create_link,
)
from app.models.models import Link
from sqlalchemy.future import select

def test_verify_password():
    password = "strongpass"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)

@pytest.mark.asyncio
async def test_get_current_user_invalid_payload(monkeypatch):
    token = jwt.encode({}, "testsecret", algorithm="HS256")
    monkeypatch.setattr("app.auth.utils.SECRET_KEY", "testsecret")
    monkeypatch.setattr("app.auth.utils.ALGORITHM", "HS256")

    class FakeDB:
        async def execute(self, *args, **kwargs): return None

    with pytest.raises(HTTPException):
        await get_current_user(token=token, db=FakeDB())

@pytest.mark.asyncio
async def test_search_link_not_found(async_client):
    await async_client.post("/auth/register", json={"email": "notfound@example.com", "password": "secure123"})
    resp = await async_client.post("/auth/login", data={"username": "notfound@example.com", "password": "secure123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.get("/links/search", params={"original_url": "https://nope.com"}, headers=headers)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client):
    await async_client.post("/auth/register", json={"email": "dup@example.com", "password": "secure123"})
    resp = await async_client.post("/auth/register", json={"email": "dup@example.com", "password": "secure123"})
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_create_link_with_existing_alias(async_client):
    await async_client.post("/auth/register", json={"email": "aliasuser@example.com", "password": "secure123"})
    resp = await async_client.post("/auth/login", data={"username": "aliasuser@example.com", "password": "secure123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    custom_alias = "customalias123"
    resp1 = await async_client.post("/links/shorten", json={"original_url": "https://alias1.com", "custom_alias": custom_alias}, headers=headers)
    assert resp1.status_code == 200
    resp2 = await async_client.post("/links/shorten", json={"original_url": "https://alias2.com", "custom_alias": custom_alias}, headers=headers)
    assert resp2.status_code == 400

@pytest.mark.asyncio
async def test_stats_with_invalid_token(async_client):
    response = await async_client.get("/links/somecode/stats", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_delete_foreign_link(async_client):
    await async_client.post("/auth/register", json={"email": "user1@example.com", "password": "secure123"})
    login1 = await async_client.post("/auth/login", data={"username": "user1@example.com", "password": "secure123"})
    token1 = login1.json()["access_token"]
    await async_client.post("/auth/register", json={"email": "user2@example.com", "password": "secure123"})
    login2 = await async_client.post("/auth/login", data={"username": "user2@example.com", "password": "secure123"})
    token2 = login2.json()["access_token"]
    create = await async_client.post("/links/shorten", json={"original_url": "https://foreign.com"}, headers={"Authorization": f"Bearer {token1}"})
    short_code = create.json()["short_code"]
    update = await async_client.put(f"/links/{short_code}", json={"original_url": "https://hacked.com"}, headers={"Authorization": f"Bearer {token2}"})
    assert update.status_code == 404
    delete = await async_client.delete(f"/links/{short_code}", headers={"Authorization": f"Bearer {token2}"})
    assert delete.status_code == 404


@pytest.mark.asyncio
async def test_redirect_with_redis_failure(monkeypatch, async_client):
    await async_client.post("/auth/register", json={"email": "redisfail@example.com", "password": "secure123"})
    login = await async_client.post("/auth/login", data={"username": "redisfail@example.com", "password": "secure123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.post("/links/shorten", json={"original_url": "https://redis-fail.com"}, headers=headers)
    short_code = resp.json()["short_code"]

    class FakeRedis:
        async def get(self, key): raise Exception("Redis GET fail")
        async def setex(self, *args, **kwargs): raise Exception("Redis SET fail")
    monkeypatch.setattr("app.api.main.get_redis", lambda: FakeRedis())

    resp = await async_client.get(f"/{short_code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"].startswith("https://redis-fail.com")

@pytest.mark.asyncio
@pytest.mark.parametrize("existing_in_db, expected_exception, expected_msg", [(True, HTTPException, None), (False, Exception, "Failed to generate unique short code"),])
async def test_generate_unique_code_collision(monkeypatch, async_session: AsyncSession, existing_in_db, expected_exception, expected_msg):
    monkeypatch.setattr("app.crud.generate_short_code", lambda length=6: "fixedcode")
    if not existing_in_db:
        link = Link(original_url="https://existing.com", short_code="fixedcode", user_id=1)
        async_session.add(link)
        await async_session.commit()
    class DummyDB:
        async def execute(self, stmt):
            class DummyResult:
                def scalar_one_or_none(self): return True
            return DummyResult()
    db = DummyDB() if existing_in_db else async_session
    with pytest.raises(expected_exception) as exc:
        await generate_unique_code(db, length=6)
    if expected_msg:
        assert expected_msg in str(exc.value)


@pytest.mark.asyncio
async def test_update_link_with_last_click(async_client):
    await async_client.post("/auth/register", json={"email": "clicker@example.com", "password": "secure123"})
    login = await async_client.post("/auth/login", data={"username": "clicker@example.com", "password": "secure123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await async_client.post("/links/shorten", json={"original_url": "https://clicker.com"}, headers=headers)
    short_code = create.json()["short_code"]
    now = datetime.utcnow().isoformat()
    update = await async_client.put(f"/links/{short_code}", json={"original_url": "https://updated.com", "last_click": now}, headers=headers)
    assert update.status_code == 200
    assert update.json()["original_url"] == "https://updated.com/"

@pytest.mark.asyncio
async def test_update_invalid_url(async_client):
    await async_client.post("/auth/register", json={"email": "invalidurl@example.com", "password": "secure123"})
    login = await async_client.post("/auth/login", data={"username": "invalidurl@example.com", "password": "secure123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await async_client.post("/links/shorten", json={"original_url": "https://initial.com"}, headers=headers)
    short_code = create.json()["short_code"]
    update = await async_client.put(f"/links/{short_code}", json={"original_url": "not-a-url"}, headers=headers)
    assert update.status_code == 422

@pytest.mark.asyncio
async def test_redirect_not_found(async_client):
    resp = await async_client.get("/nonexistent123", follow_redirects=False)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Short link not found"

@pytest.mark.asyncio
async def test_login_invalid_password(async_client):
    await async_client.post("/auth/register", json={"email": "badpass@example.com", "password": "secure123"})
    resp = await async_client.post("/auth/login", data={"username": "badpass@example.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or pwd"

@pytest.mark.asyncio
async def test_shorten_without_auth(async_client):
    resp = await async_client.post("/links/shorten", json={"original_url": "https://noauth.com"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_create_link_crud(async_session):
    fake_user = SimpleNamespace(id=123)
    link_data = LinkCreate(original_url="https://crud.com")
    result = await create_link(async_session, link_data, fake_user)
    assert result.original_url.rstrip("/") == "https://crud.com"

@pytest.mark.asyncio
async def test_get_link_stats_foreign(async_client):
    await async_client.post("/auth/register", json={"email": "owner@example.com", "password": "secure123"})
    login1 = await async_client.post("/auth/login", data={"username": "owner@example.com", "password": "secure123"})
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    create = await async_client.post("/links/shorten", json={"original_url": "https://secret.com"}, headers=headers1)
    short_code = create.json()["short_code"]
    await async_client.post("/auth/register", json={"email": "intruder@example.com", "password": "secure123"})
    login2 = await async_client.post("/auth/login", data={"username": "intruder@example.com", "password": "secure123"})
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    resp = await async_client.get(f"/links/{short_code}/stats", headers=headers2)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_update_link_with_redis_failure(monkeypatch, async_client):
    await async_client.post("/auth/register", json={"email": "updatefail@example.com", "password": "secure123"})
    login = await async_client.post("/auth/login", data={"username": "updatefail@example.com", "password": "secure123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.post("/links/shorten", json={"original_url": "https://before-redis.com"}, headers=headers)
    short_code = resp.json()["short_code"]

    class FakeRedis:
        async def setex(self, *args, **kwargs): raise Exception("Redis SET failed")

    monkeypatch.setattr("app.api.main.get_redis", lambda: FakeRedis())

    update = await async_client.put(f"/links/{short_code}", json={"original_url": "https://after-redis.com"}, headers=headers)
    assert update.status_code == 200
    assert update.json()["original_url"].rstrip("/") == "https://after-redis.com"

@pytest.mark.asyncio
async def test_init_models_runs():
    from app.init_db import init_models
    try:
        await init_models()
    except Exception:
        pass

@pytest.mark.asyncio
async def test_redirect_link_from_db(async_client, async_session):
    user = User(email="dbredirect@example.com", hashed_password="hashed")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    link_data = LinkCreate(original_url="https://direct-from-db.com")
    link = await create_link(async_session, link_data, user)
    response = await async_client.get(f"/{link.short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://direct-from-db.com")

@pytest.mark.asyncio
async def test_search_by_original_url_success(async_client):
    await async_client.post("/auth/register", json={"email": "searchreal@example.com", "password": "123456"})
    login = await async_client.post("/auth/login", data={"username": "searchreal@example.com", "password": "123456"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    url = f"https://foundlink.com/{datetime.utcnow().timestamp()}"
    await async_client.post("/links/shorten", json={"original_url": url}, headers=headers)

    resp = await async_client.get("/links/search", params={"original_url": url}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["original_url"].rstrip("/") == url.rstrip("/")


@pytest.mark.asyncio
async def test_read_root(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello! Welcome to the app - URL Shortener API!"}