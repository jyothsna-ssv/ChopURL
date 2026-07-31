from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    REDIS_URL: str = "redis://localhost:6379"
    
    # Application
    APP_NAME: str = "ChopURL"
    DEBUG: bool = False
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    # URL Settings
    BASE_URL: str = "http://localhost:8000"
    SHORT_URL_LENGTH: int = 6
    BLOCKED_HOSTS: List[str] = []
    USER_CREATE_LIMIT_PER_DAY: int = 100
    ANONYMOUS_CREATE_LIMIT_PER_DAY: int = 20
    SHORTEN_RATE_LIMIT: str = "10/minute"
    REDIRECT_RATE_LIMIT: str = "120/minute"
    STATS_RATE_LIMIT: str = "60/minute"
    ADMIN_RATE_LIMIT: str = "60/minute"
    
    # Supabase
    SUPABASE_URL: str = ""  # User will fill in
    SUPABASE_ANON_KEY: str = ""  # User will fill in
    SUPABASE_JWT_SECRET: str = ""  # User will fill in from Supabase dashboard
    
    class Config:
        env_file = ".env"

settings = Settings()
