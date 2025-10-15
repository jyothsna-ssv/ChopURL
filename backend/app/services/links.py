from app.db.redis_client import redis_client
from app.utils.hashids import generate_short_code
from app.core.config import settings
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

class LinkService:
    def __init__(self):
        self.redis = redis_client
        self.base_url = settings.BASE_URL
    
    async def create_short_url(self, original_url: str, custom_code: str = None) -> str:
        """Create a shortened URL and store it in Redis"""
        # If custom code is provided, use it
        if custom_code:
            # Check if custom code already exists
            existing_link = await self.redis.get(f"short:{custom_code}")
            if existing_link:
                raise ValueError(f"Custom code '{custom_code}' already exists")
            
            short_code = custom_code
        else:
            # Check if URL already exists
            existing_short_code = await self._get_existing_short_code(original_url)
            if existing_short_code:
                return f"{self.base_url}/{existing_short_code}"
            
            # Generate new short code
            short_code = generate_short_code()
        
        # Store in Redis with expiration (e.g., 1 year)
        link_data = {
            "original_url": original_url,
            "created_at": str(datetime.utcnow()),
            "clicks": 0
        }
        
        await self.redis.setex(
            f"short:{short_code}",
            31536000,  # 1 year in seconds
            json.dumps(link_data)
        )
        
        # Store reverse mapping for deduplication (only if no custom code)
        if not custom_code:
            await self.redis.setex(
                f"url:{original_url}",
                31536000,
                short_code
            )
        
        return f"{self.base_url}/{short_code}"
    
    async def get_original_url(self, short_code: str) -> Optional[str]:
        """Get the original URL for a short code"""
        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            return None
        
        data = json.loads(link_data)
        
        # Increment click count
        data["clicks"] += 1
        await self.redis.setex(
            f"short:{short_code}",
            31536000,
            json.dumps(data)
        )
        
        return data["original_url"]
    
    async def get_url_stats(self, short_code: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a shortened URL"""
        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            return None
        
        data = json.loads(link_data)
        return {
            "short_code": short_code,
            "original_url": data["original_url"],
            "clicks": data["clicks"],
            "created_at": data["created_at"]
        }
    
    async def _get_existing_short_code(self, original_url: str) -> Optional[str]:
        """Check if URL already has a short code"""
        return await self.redis.get(f"url:{original_url}")
    
    async def get_all_links(self, skip: int = 0, limit: int = 15) -> List[Dict[str, Any]]:
        """Get all shortened links for admin panel with pagination"""
        try:
            # Get all keys that start with "short:"
            keys = await self.redis.keys("short:*")
            links = []
            
            for key in keys:
                link_data = await self.redis.get(key)
                if link_data:
                    data = json.loads(link_data)
                    short_code = key.replace("short:", "")
                    links.append({
                        "short_code": short_code,
                        "original_url": data["original_url"],
                        "short_url": f"{self.base_url}/{short_code}",
                        "clicks": data["clicks"],
                        "created_at": data["created_at"]
                    })
            
            # Sort by creation date (newest first)
            links.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            return links[skip:skip + limit]
        except Exception as e:
            print(f"Error getting all links: {e}")
            return []
    
    async def delete_link(self, short_code: str) -> bool:
        """Delete a specific shortened link"""
        try:
            # Get the original URL first
            link_data = await self.redis.get(f"short:{short_code}")
            if not link_data:
                return False
            
            data = json.loads(link_data)
            original_url = data["original_url"]
            
            # Delete both the short code and reverse mapping
            await self.redis.delete(f"short:{short_code}")
            await self.redis.delete(f"url:{original_url}")
            
            return True
        except Exception as e:
            print(f"Error deleting link: {e}")
            return False
    
    async def clear_all_links(self) -> bool:
        """Clear all shortened links"""
        try:
            # Get all keys that start with "short:" or "url:"
            keys = await self.redis.keys("short:*")
            url_keys = await self.redis.keys("url:*")
            
            # Delete all keys
            if keys:
                await self.redis.delete(*keys)
            if url_keys:
                await self.redis.delete(*url_keys)
            
            return True
        except Exception as e:
            print(f"Error clearing all links: {e}")
            return False
