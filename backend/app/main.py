import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from redis.exceptions import RedisError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.routers import router
from app.core.config import settings
from app.core.rate_limit import limiter

logger = logging.getLogger("chopurl")

app = FastAPI(
    title="ChopURL API",
    description="A URL shortening service",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RedisError)
async def redis_error_handler(request: Request, exc: RedisError):
    logger.exception(
        "redis_dependency_unavailable",
        extra={"path": request.url.path, "method": request.method},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "A required service is temporarily unavailable", "error_code": "dependency_unavailable"},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled_application_error",
        extra={"path": request.url.path, "method": request.method},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "internal_error"},
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "ChopURL API is running"}

@app.get("/health")
async def health_check():
    from app.db.redis_client import redis_client

    await redis_client.ping()
    supabase_ready = bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)
    if not supabase_ready:
        raise HTTPException(status_code=503, detail="Authentication dependency is not configured")
    return {"status": "ready", "checks": {"redis": "ok", "supabase_auth": "ok"}}


@app.get("/health/live")
async def liveness_check():
    return {"status": "alive"}

# Add redirect endpoint at root level (must be last to avoid conflicts)
from app.services.links import LinkService

@app.get("/{short_code}")
@limiter.limit(settings.REDIRECT_RATE_LIMIT)
async def redirect_url(request: Request, short_code: str):
    """Redirect to original URL"""
    link_service = LinkService()
    original_url = await link_service.get_original_url(short_code)
    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found")

    return RedirectResponse(url=original_url, status_code=302)
