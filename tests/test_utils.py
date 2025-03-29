import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException
from app.auth.utils import create_access_token, get_current_user

ALGORITHM = "HS256"
SECRET_KEY = "testsecret"


class FakeSession:
    async def get(self, *args, **kwargs):
        return None


def test_create_access_token(monkeypatch):
    monkeypatch.setattr("app.auth.utils.SECRET_KEY", SECRET_KEY)
    token = create_access_token(data={"sub": "user@example.com"}, expires_delta=timedelta(minutes=5))
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user@example.com"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    monkeypatch.setattr("app.auth.utils.SECRET_KEY", SECRET_KEY)
    monkeypatch.setattr("app.auth.utils.ALGORITHM", ALGORITHM)

    invalid_token = "invalid.token.here"

    with pytest.raises(HTTPException):
        await get_current_user(token=invalid_token, db=FakeSession())