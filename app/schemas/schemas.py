from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class LinkCreate(BaseModel):
    original_url: HttpUrl
    short_code: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkInfo(BaseModel):
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int
    last_click: Optional[datetime]

    class Config:
        orm_mode = True

class LinkUpdate(BaseModel):
    original_url: str