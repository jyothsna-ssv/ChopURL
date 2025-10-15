from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class URLRequest(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None
    
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
