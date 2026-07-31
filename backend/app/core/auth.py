from fastapi import Header, HTTPException
import httpx
import jwt
from app.core.config import settings


async def _get_supabase_user_id(token: str) -> str:
    """Validate a Supabase access token and return the user id."""
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
            user_id = payload.get("sub")
            if user_id:
                return user_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            pass

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_ANON_KEY,
                },
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=401, detail="Unable to verify session")

    if response.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Invalid token")
    if response.status_code >= 400:
        raise HTTPException(status_code=401, detail="Unable to verify session")

    user = response.json()
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


async def get_current_user(authorization: str = Header(None)) -> str:
    """Require authenticated user and return user_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ", 1)[1]
    return await _get_supabase_user_id(token)


async def get_optional_user(authorization: str = Header(None)):
    """Optionally authenticate user. Returns user_id or None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ", 1)[1]
    try:
        return await _get_supabase_user_id(token)
    except HTTPException:
        return None
