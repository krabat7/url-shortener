import os
from redis import asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis