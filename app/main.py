from app.api.main import router as link_router
from app.auth.auth import router as auth_router
from fastapi import FastAPI
import os

app = FastAPI(title="URL Shortener")

app.include_router(link_router)
app.include_router(auth_router)

if os.getenv("INIT_DB_ON_STARTUP") == "true":
    from app.init_db import init_models
    import asyncio

    asyncio.run(init_models())