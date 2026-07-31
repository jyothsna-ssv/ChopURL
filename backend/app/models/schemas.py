from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional

class URLRequest(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Optional memorable short code using letters, numbers, underscores, or hyphens."
    )

    @field_validator("custom_code", mode="before")
    @classmethod
    def normalize_custom_code(cls, value):
        if value is None:
            return value
        if not isinstance(value, str):
            return value
        return value.strip().lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/very/long/url",
                "custom_code": "my-custom-code"
            }
        }

class URLResponse(BaseModel):
    original_url: str
    short_url: str
    short_code: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://example.com/very/long/url",
                "short_url": "http://localhost:8000/abc123",
                "short_code": "abc123"
            }
        }

class URLStats(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "short_code": "abc123",
                "original_url": "https://example.com/very/long/url",
                "clicks": 42,
                "created_at": "2024-01-01T00:00:00"
            }
        }

class LinkItem(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    clicks: int
    created_at: str

class LinksPageResponse(BaseModel):
    items: List[LinkItem]
    total: int
    skip: int
    limit: int
    total_clicks: int
    average_clicks: float

class UserInfo(BaseModel):
    user_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "uuid-string"
            }
        }
