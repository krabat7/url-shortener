import random
import string

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import Link, User


def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def generate_unique_code(db: AsyncSession, length=6):
    for _ in range(5):
        code = generate_short_code(length)
        result = await db.execute(select(Link).where(Link.short_code == code))
        if not result.scalar_one_or_none():
            return code
    raise HTTPException(status_code=500, detail="Failed to generate unique short code")


async def create_link(db: AsyncSession, link_data, user: User):
    custom_alias = getattr(link_data, "custom_alias", None)
    if custom_alias:
        existing = await db.execute(select(Link).where(Link.short_code == custom_alias))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Custom alias already taken")
        short_code = custom_alias
    else:
        short_code = await generate_unique_code(db)

    new_link = Link(
        original_url=str(link_data.original_url),
        short_code=short_code,
        expires_at=link_data.expires_at,
        user_id=user.id
    )

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link