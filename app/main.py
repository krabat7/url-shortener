from app.api.main import router as link_router
from app.auth.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI(title="URL Shortener")

app.include_router(link_router)
app.include_router(auth_router)