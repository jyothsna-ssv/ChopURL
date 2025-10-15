from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import router
from app.core.config import settings

app = FastAPI(
    title="ChopURL API",
    description="A URL shortening service",
    version="1.0.0"
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
    return {"status": "healthy"}

# Add redirect endpoint at root level (must be last to avoid conflicts)
from app.services.links import LinkService
from fastapi import HTTPException

@app.get("/{short_code}")
async def redirect_url(short_code: str):
    """Redirect to original URL"""
    try:
        link_service = LinkService()
        original_url = await link_service.get_original_url(short_code)
        if not original_url:
            raise HTTPException(status_code=404, detail="URL not found")
        
        # Perform actual HTTP redirect
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=original_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
