from fastapi import APIRouter, HTTPException, Depends, Header
from app.models.schemas import URLRequest, URLResponse
from app.services.links import LinkService
from app.core.config import settings
from app.core.auth import get_current_user, get_optional_user

router = APIRouter()

@router.post("/shorten", response_model=URLResponse)
async def shorten_url(request: URLRequest, user_id: str = Depends(get_optional_user)):
    """Create a shortened URL"""
    try:
        link_service = LinkService()
        url_str = str(request.url)
        short_url = await link_service.create_short_url(url_str, request.custom_code, user_id=user_id)
        return URLResponse(
            original_url=url_str,
            short_url=short_url,
            short_code=short_url.split("/")[-1]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{short_code}")
async def redirect_url(short_code: str):
    """Redirect to original URL"""
    try:
        link_service = LinkService()
        original_url = await link_service.get_original_url(short_code)
        if not original_url:
            raise HTTPException(status_code=404, detail="URL not found")
        return {"redirect_url": original_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{short_code}")
async def get_url_stats(short_code: str):
    """Get statistics for a shortened URL"""
    try:
        link_service = LinkService()
        stats = await link_service.get_url_stats(short_code)
        if not stats:
            raise HTTPException(status_code=404, detail="URL not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@router.get("/admin/links")
async def get_all_links(skip: int = 0, limit: int = 15, user_id: str = Depends(get_current_user)):
    """Get user's shortened links with pagination"""
    try:
        link_service = LinkService()
        links = await link_service.get_all_links(skip=skip, limit=limit, user_id=user_id)
        return links
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/links/{short_code}")
async def delete_link(short_code: str, user_id: str = Depends(get_current_user)):
    """Delete a specific shortened link (owner only)"""
    try:
        link_service = LinkService()
        success = await link_service.delete_link(short_code, user_id=user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Link not found or not owned by you")
        return {"message": "Link deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/links/clear/all")
async def clear_all_links(user_id: str = Depends(get_current_user)):
    """Clear all of the user's shortened links"""
    try:
        link_service = LinkService()
        await link_service.clear_all_links(user_id=user_id)
        return {"message": "All your links cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/me")
async def get_me(user_id: str = Depends(get_current_user)):
    """Get current user info"""
    return {"user_id": user_id}
