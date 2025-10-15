from fastapi import APIRouter, HTTPException, Depends, Header
from app.models.schemas import URLRequest, URLResponse
from app.services.links import LinkService
from app.core.config import settings

router = APIRouter()

@router.post("/shorten", response_model=URLResponse)
async def shorten_url(request: URLRequest):
    """Create a shortened URL"""
    try:
        link_service = LinkService()
        # Convert HttpUrl to string
        url_str = str(request.url)
        short_url = await link_service.create_short_url(url_str, request.custom_code)
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
async def get_all_links(skip: int = 0, limit: int = 15):
    """Get all shortened links with pagination (admin only)"""
    try:
        link_service = LinkService()
        links = await link_service.get_all_links(skip=skip, limit=limit)
        return links
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/links/{short_code}")
async def delete_link(short_code: str):
    """Delete a specific shortened link (admin only)"""
    try:
        link_service = LinkService()
        success = await link_service.delete_link(short_code)
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Link deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/links/clear/all")
async def clear_all_links():
    """Clear all shortened links (admin only)"""
    try:
        link_service = LinkService()
        await link_service.clear_all_links()
        return {"message": "All links cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
