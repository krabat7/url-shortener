from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class LinkCreate(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
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