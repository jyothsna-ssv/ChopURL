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
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    # URL Settings
    BASE_URL: str = "http://localhost:8000"
    SHORT_URL_LENGTH: int = 6
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    
    class Config:
        env_file = ".env"

settings = Settings()
