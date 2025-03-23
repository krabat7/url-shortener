import random, string
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Link, User
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.future import select

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def create_link(db: AsyncSession, link_data, current_user: User):
    if link_data.custom_alias:
        result = await db.execute(select(Link).where(Link.short_code == link_data.custom_alias))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Custom alias already in use")

    short_code = link_data.custom_alias or generate_short_code()
    
    db_link = Link(
        original_url=link_data.original_url,
        short_code=short_code,
        created_at=datetime.utcnow(),
        expires_at=link_data.expires_at,
        click_count=0,
        last_click=None,
        user_id=current_user.id
    )
    
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link