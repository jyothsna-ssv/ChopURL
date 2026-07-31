from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def create_limiter(storage_uri: str | None = None) -> Limiter:
    """Build a limiter backed by the configured Redis instance."""
    return Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri or settings.REDIS_URL,
        strategy="fixed-window",
    )


limiter = create_limiter()
