import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Redis connection
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)
