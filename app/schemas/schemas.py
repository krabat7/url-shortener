from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
from datetime import datetime

class LinkCreate(BaseModel):
    original_url: HttpUrl
    short_code: Optional[str] = None
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LinkInfo(BaseModel):
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int
    last_click: Optional[datetime]

    class Config:
        from_attributes = True

class LinkUpdate(BaseModel):
    original_url: HttpUrl
    last_click: Optional[datetime] = None

    @field_validator("last_click", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v