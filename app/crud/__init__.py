import random, string
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Link, User
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.future import select

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def create_link(db, link_data, user):
    # Если short_code не указан — генерируем
    short_code = link_data.short_code or await generate_unique_code(db)

    new_link = Link(
        original_url=link_data.original_url,
        short_code=short_code,
        expires_at=link_data.expires_at,
        user_id=user.id
    )

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link

async def generate_unique_code(db, length=6):
    for _ in range(5):  # до 5 попыток
        code = generate_short_code(length)
        result = await db.execute(select(Link).where(Link.short_code == code))
        if not result.scalar_one_or_none():
            return code
    raise HTTPException(status_code=500, detail="Failed to generate unique short code")