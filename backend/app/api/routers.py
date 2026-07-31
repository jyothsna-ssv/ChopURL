import logging

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from app.core.errors import (
    LinkNotFoundError,
    LinkOwnershipError,
    LinkValidationError,
    ShortCodeConflictError,
    ShortCodeGenerationError,
)
from app.models.schemas import LinksPageResponse, URLRequest, URLResponse
from app.services.links import LinkService, QuotaExceededError
from app.core.auth import get_current_user, get_optional_user
from app.core.config import settings
from app.core.rate_limit import limiter
from slowapi.util import get_remote_address

router = APIRouter()
logger = logging.getLogger("chopurl.api")

@router.post("/shorten", response_model=URLResponse)
@limiter.limit(settings.SHORTEN_RATE_LIMIT)
async def shorten_url(request: Request, payload: URLRequest, user_id: str = Depends(get_optional_user)):
    """Create a shortened URL"""
    try:
        link_service = LinkService()
        url_str = str(payload.url)
        quota_key = f"user:{user_id}" if user_id else f"ip:{get_remote_address(request)}"
        short_url = await link_service.create_short_url(
            url_str,
            payload.custom_code,
            user_id=user_id,
            quota_key=quota_key,
        )
        return URLResponse(
            original_url=url_str,
            short_url=short_url,
            short_code=short_url.split("/")[-1]
        )
    except QuotaExceededError:
        raise HTTPException(status_code=429, detail="Daily link creation limit reached")
    except ShortCodeConflictError:
        raise HTTPException(status_code=409, detail="Custom code is already in use")
    except LinkValidationError as error:
        raise HTTPException(status_code=400, detail=error.args[0])
    except ShortCodeGenerationError:
        logger.error("short_code_generation_exhausted")
        raise HTTPException(status_code=503, detail="Unable to allocate a short code. Please try again.")

@router.get("/{short_code}")
@limiter.limit(settings.REDIRECT_RATE_LIMIT)
async def redirect_url(request: Request, short_code: str):
    """Redirect to original URL"""
    link_service = LinkService()
    original_url = await link_service.get_original_url(short_code)
    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"redirect_url": original_url}

@router.get("/stats/{short_code}")
@limiter.limit(settings.STATS_RATE_LIMIT)
async def get_url_stats(request: Request, short_code: str, user_id: str = Depends(get_optional_user)):
    """Get statistics for a shortened URL"""
    link_service = LinkService()
    stats = await link_service.get_url_stats(short_code, user_id=user_id)
    if not stats:
        raise HTTPException(status_code=404, detail="URL not found")
    return stats

# Admin endpoints
@router.get("/admin/links", response_model=LinksPageResponse)
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def get_all_links(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=15, ge=1, le=100),
    user_id: str = Depends(get_current_user)
):
    """Get user's shortened links with pagination"""
    link_service = LinkService()
    return await link_service.get_all_links(skip=skip, limit=limit, user_id=user_id)

@router.delete("/admin/links/{short_code}")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def delete_link(request: Request, short_code: str, user_id: str = Depends(get_current_user)):
    """Delete a specific shortened link (owner only)"""
    try:
        link_service = LinkService()
        await link_service.delete_link(short_code, user_id=user_id)
        return {"message": "Link deleted successfully"}
    except LinkNotFoundError:
        raise HTTPException(status_code=404, detail="Link not found")
    except LinkOwnershipError:
        raise HTTPException(status_code=404, detail="Link not found")

@router.delete("/admin/links/clear/all")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def clear_all_links(request: Request, user_id: str = Depends(get_current_user)):
    """Clear all of the user's shortened links"""
    link_service = LinkService()
    await link_service.clear_all_links(user_id=user_id)
    return {"message": "All your links cleared successfully"}

@router.get("/auth/me")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def get_me(request: Request, user_id: str = Depends(get_current_user)):
    """Get current user info"""
    return {"user_id": user_id}
