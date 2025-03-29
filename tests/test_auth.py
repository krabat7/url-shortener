import pytest

@pytest.mark.asyncio
async def test_register_and_login(async_client):
    response = await async_client.post("/auth/register", json={
        "email": "testuser@example.com",
        "password": "pwd1337"
    })
    assert response.status_code == 200

    response = await async_client.post("/auth/login", data={
        "username": "testuser@example.com",
        "password": "pwd1337"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_existing_email(async_client):
    await async_client.post("/auth/register", json={
        "email": "dupuser@example.com",
        "password": "dup12345"
    })
    response = await async_client.post("/auth/register", json={
        "email": "dupuser@example.com",
        "password": "dup12345"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_invalid_email(async_client):
    response = await async_client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "somepassword"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(async_client):
    response = await async_client.post("/auth/register", json={
        "email": "shortpass@example.com",
        "password": "12"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_no_data(async_client):
    response = await async_client.post("/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_user(async_client):
    response = await async_client.post("/auth/login", data={
        "username": "notexists@example.com",
        "password": "somepass"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(async_client):
    await async_client.post("/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "correctpass"
    })
    response = await async_client.post("/auth/login", data={
        "username": "wrongpass@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client):
    response = await async_client.post("/auth/login", data={
        "username": "ghost@example.com",
        "password": "whatever"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or pwd"


@pytest.mark.asyncio
async def test_login_missing_fields(async_client):
    response = await async_client.post("/auth/login", data={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_nonexistent_user_wrong_pass(async_client):
    await async_client.post("/auth/register", json={
        "email": "combo@example.com",
        "password": "realpass"
    })
    response = await async_client.post("/auth/login", data={
        "username": "combo@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client):
    await async_client.post("/auth/register", json={"email": "wrong@example.com", "password": "correctpass"})

    resp = await async_client.post("/auth/login", data={
        "username": "wrong@example.com",
        "password": "wrongpass"
    })
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or pwd"