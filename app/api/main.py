from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from app.schemas.schemas import LinkCreate, LinkInfo, LinkUpdate
from app.models.models import Link, User
from app.db import get_db
from app.redis_cache import get_redis
from app.auth.utils import get_current_user
from app.crud import create_link

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "Hello! Welcome to the app - URL Shortener API!"}


@router.post("/links/shorten", response_model=LinkInfo)
async def shorten_link(link: LinkCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await create_link(db, link, current_user)


@router.get("/{short_code}")
async def redirect_link(short_code: str, db: AsyncSession = Depends(get_db)):
    cached_url = None
    try:
        redis = await get_redis()
        cached_url = await redis.get(short_code)
    except Exception as e:
        print(f"[Redis] GET failed: {e}")

    if cached_url:
        return RedirectResponse(cached_url)

    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link has expired")

    link.click_count += 1
    link.last_click = datetime.utcnow()
    await db.commit()

    try:
        redis = await get_redis()
        await redis.setex(short_code, 3600, link.original_url)
    except Exception as e:
        print(f"[Redis] SET failed: {e}")

    return RedirectResponse(link.original_url)


@router.delete("/links/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(short_code: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found or not yours")

    await db.delete(link)
    await db.commit()

    try:
        redis = await get_redis()
        await redis.delete(short_code)
    except Exception as e:
        print(f"[Redis] DELETE failed: {e}")


@router.put("/links/{short_code}", response_model=LinkInfo)
async def update_link(short_code: str, update_data: LinkUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found or not yours")

    link.original_url = update_data.original_url
    await db.commit()
    await db.refresh(link)

    try:
        redis = await get_redis()
        await redis.setex(short_code, 3600, link.original_url)
    except Exception as e:
        print(f"[Redis] SET failed: {e}")

    return link


@router.get("/links/{short_code}/stats", response_model=LinkInfo)
async def get_link_stats(short_code: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link or link.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Link not found or not yours")
    return link


@router.get("/links/expired", response_model=list[LinkInfo])
async def get_expired_links(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    result = await db.execute(select(Link).where(Link.expires_at.is_not(None), Link.expires_at < now))
    return result.scalars().all()


@router.delete("/links/cleanup", status_code=status.HTTP_204_NO_CONTENT)
async def delete_old_links(days: int = Query(..., gt=0), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Link).where(((Link.last_click < cutoff_date) | (Link.last_click.is_(None))) & (Link.user_id == current_user.id))
    )
    old_links = result.scalars().all()
    for link in old_links:
        await db.delete(link)
        try:
            redis = await get_redis()
            await redis.delete(link.short_code)
        except Exception as e:
            print(f"[Redis] DELETE in cleanup failed: {e}")
    await db.commit()


@router.get("/links/search", response_model=LinkInfo)
async def search_by_original_url(original_url: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Link).where(Link.original_url == original_url, Link.user_id == current_user.id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link