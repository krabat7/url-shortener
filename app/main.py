from fastapi import FastAPI
from app.api.main import router as link_router
from app.auth.auth import router as auth_router
import os
from app.init_db import init_models
import asyncio

app = FastAPI(title="URL Shortener")

app.include_router(link_router)
app.include_router(auth_router)

@app.on_event("startup")
async def on_startup():
    if os.getenv("INIT_DB_ON_STARTUP") == "true":
        await init_models()