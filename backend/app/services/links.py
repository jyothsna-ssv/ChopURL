from app.db.redis_client import redis_client
from app.utils.hashids import generate_short_code
from app.core.config import settings
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

class LinkService:
    def __init__(self):
        self.redis = redis_client
        self.base_url = settings.BASE_URL
    
    async def create_short_url(self, original_url: str, custom_code: str = None, user_id: str = None) -> str:
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
            "created_at": str(datetime.now(timezone.utc)),
            "clicks": 0,
            "last_clicked": None,
            "click_history": [],
            "user_id": user_id
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
            
        if user_id:
            await self.redis.sadd(f"user_links:{user_id}", short_code)
        
        return f"{self.base_url}/{short_code}"
    
    async def get_original_url(self, short_code: str) -> Optional[str]:
        """Get the original URL for a short code"""
        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            return None
        
        data = json.loads(link_data)
        
        now = str(datetime.now(timezone.utc))
        
        # Increment click count and record timestamp
        data["clicks"] += 1
        data["last_clicked"] = now
        
        # Initialize click_history if it doesn't exist (for older links)
        if "click_history" not in data:
            data["click_history"] = []
        
        # Add timestamp to click history (keep last 50)
        data["click_history"].append(now)
        data["click_history"] = data["click_history"][-50:]
        
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
            "short_url": f"{self.base_url}/{short_code}",
            "clicks": data["clicks"],
            "created_at": data["created_at"],
            "last_clicked": data.get("last_clicked"),
            "click_history": data.get("click_history", [])
        }
    
    async def _get_existing_short_code(self, original_url: str) -> Optional[str]:
        """Check if URL already has a short code"""
        return await self.redis.get(f"url:{original_url}")
    
    async def get_all_links(self, skip: int = 0, limit: int = 15, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all shortened links for admin panel with pagination"""
        try:
            if user_id:
                # Get only this user's links
                short_codes = await self.redis.smembers(f"user_links:{user_id}")
                keys = [f"short:{code}" for code in short_codes]
            else:
                keys = await self.redis.keys("short:*")
            
            links = []
            for key in keys:
                link_data = await self.redis.get(key)
                if link_data:
                    data = json.loads(link_data)
                    short_code = key.replace("short:", "") if isinstance(key, str) and key.startswith("short:") else key
                    links.append({
                        "short_code": short_code,
                        "original_url": data["original_url"],
                        "short_url": f"{self.base_url}/{short_code}",
                        "clicks": data["clicks"],
                        "created_at": data["created_at"]
                    })
            
            links.sort(key=lambda x: x["created_at"], reverse=True)
            return links[skip:skip + limit]
        except Exception as e:
            print(f"Error getting all links: {e}")
            return []
    
    async def delete_link(self, short_code: str, user_id: str = None) -> bool:
        """Delete a specific shortened link"""
        try:
            link_data = await self.redis.get(f"short:{short_code}")
            if not link_data:
                return False
            
            data = json.loads(link_data)
            
            # If user_id provided, verify ownership
            if user_id and data.get("user_id") != user_id:
                return False
            
            original_url = data["original_url"]
            owner_id = data.get("user_id")
            
            await self.redis.delete(f"short:{short_code}")
            await self.redis.delete(f"url:{original_url}")
            
            # Remove from user's link set
            if owner_id:
                await self.redis.srem(f"user_links:{owner_id}", short_code)
            
            return True
        except Exception as e:
            print(f"Error deleting link: {e}")
            return False
    
    async def clear_all_links(self, user_id: str = None) -> bool:
        """Clear all shortened links"""
        try:
            if user_id:
                # Only clear this user's links
                short_codes = await self.redis.smembers(f"user_links:{user_id}")
                for code in short_codes:
                    link_data = await self.redis.get(f"short:{code}")
                    if link_data:
                        data = json.loads(link_data)
                        await self.redis.delete(f"url:{data['original_url']}")
                    await self.redis.delete(f"short:{code}")
                await self.redis.delete(f"user_links:{user_id}")
            else:
                keys = await self.redis.keys("short:*")
                url_keys = await self.redis.keys("url:*")
                if keys:
                    await self.redis.delete(*keys)
                if url_keys:
                    await self.redis.delete(*url_keys)
            
            return True
        except Exception as e:
            print(f"Error clearing all links: {e}")
            return False
