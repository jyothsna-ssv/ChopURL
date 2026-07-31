from app.db.redis_client import redis_client
from app.utils.hashids import generate_short_code
from app.utils.url_safety import validate_destination_url
from app.core.config import settings
from app.core.errors import LinkNotFoundError, LinkOwnershipError
from redis.exceptions import RedisError
import json
import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone

LINK_TTL_SECONDS = 31536000
CLICK_HISTORY_LIMIT = 50

SHORT_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
RESERVED_SHORT_CODES = {
    "api",
    "docs",
    "health",
    "openapi.json",
    "redoc",
    "favicon.ico",
    "robots.txt",
}

class QuotaExceededError(ValueError):
    """Raised when a caller exceeds the daily link creation quota."""

class LinkService:
    def __init__(self):
        self.redis = redis_client
        self.base_url = settings.BASE_URL
    
    async def create_short_url(
        self,
        original_url: str,
        custom_code: str = None,
        user_id: str = None,
        quota_key: str = None,
    ) -> str:
        """Create a shortened URL and store it in Redis"""
        validate_destination_url(original_url)
        if custom_code is not None:
            custom_code = custom_code.strip().lower()
        # If custom code is provided, use it
        if custom_code:
            if not SHORT_CODE_PATTERN.fullmatch(custom_code):
                raise ValueError("Custom code must be 3-32 characters and use only letters, numbers, underscores, or hyphens")

            if custom_code.lower() in RESERVED_SHORT_CODES:
                raise ValueError(f"Custom code '{custom_code}' is reserved")

            short_code = custom_code
        else:
            # Check if this URL already exists for the same owner context.
            existing_short_code = await self._get_existing_short_code(original_url, user_id)
            if existing_short_code:
                # Repair older records that have a valid owner mapping but are
                # missing from that owner's dashboard set.
                if user_id:
                    await self.redis.sadd(f"user_links:{user_id}", existing_short_code)
                return f"{self.base_url}/{existing_short_code}"
            
        # Reserve the code first. This lets duplicate aliases fail without
        # consuming quota while SET NX keeps the public reservation atomic.
        created_at = datetime.now(timezone.utc)
        link_data = {
            "original_url": original_url,
            "created_at": str(created_at),
            "clicks": 0,
            "last_clicked": None,
            "click_history": [],
            "user_id": user_id
        }
        
        if custom_code:
            created = await self._store_link_record(short_code, link_data)
            if not created:
                raise ValueError(f"Custom code '{short_code}' already exists")
        else:
            short_code = await self._store_generated_link_record(link_data)
        
        summary_updated = False
        try:
            if quota_key:
                await self._enforce_creation_quota(quota_key, user_id)

            if not custom_code:
                await self.redis.setex(
                    self._url_cache_key(original_url, user_id),
                    LINK_TTL_SECONDS,
                    short_code,
                )

            if user_id:
                await self.redis.sadd(f"user_links:{user_id}", short_code)

            await self.redis.zadd(self._links_index_key(user_id), {short_code: created_at.timestamp()})
            await self.redis.zadd(
                self._links_expiry_key(user_id),
                {short_code: created_at.timestamp() + LINK_TTL_SECONDS},
            )
            await self.redis.hset(
                self._link_stats_key(short_code),
                mapping={"clicks": 0, "last_clicked": ""},
            )
            await self.redis.expire(self._link_stats_key(short_code), LINK_TTL_SECONDS)
            await self.redis.hincrby(self._summary_key(user_id), "total_links", 1)
            summary_updated = True
            await self.redis.hsetnx(self._summary_key(user_id), "total_clicks", 0)
        except (QuotaExceededError, RedisError):
            await self._rollback_link_creation(
                short_code=short_code,
                original_url=original_url,
                user_id=user_id,
                reverse_mapping=not bool(custom_code),
                summary_updated=summary_updated,
            )
            raise
        
        return f"{self.base_url}/{short_code}"
    
    async def get_original_url(self, short_code: str) -> Optional[str]:
        """Get the original URL for a short code"""
        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            return None
        
        data = json.loads(link_data)
        await self._ensure_stats_record(short_code, data)

        now_datetime = datetime.now(timezone.utc)
        now = str(now_datetime)
        stats_key = self._link_stats_key(short_code)
        history_key = self._history_key(short_code)
        pipe = self.redis.pipeline(transaction=True)
        pipe.hincrby(stats_key, "clicks", 1)
        pipe.hset(stats_key, "last_clicked", now)
        pipe.lpush(history_key, now)
        pipe.ltrim(history_key, 0, CLICK_HISTORY_LIMIT - 1)
        pipe.expire(f"short:{short_code}", LINK_TTL_SECONDS)
        pipe.expire(stats_key, LINK_TTL_SECONDS)
        pipe.expire(history_key, LINK_TTL_SECONDS)
        pipe.expire(self._url_cache_key(data["original_url"], data.get("user_id")), LINK_TTL_SECONDS)
        pipe.zadd(
            self._links_expiry_key(data.get("user_id")),
            {short_code: now_datetime.timestamp() + LINK_TTL_SECONDS},
        )
        pipe.hincrby(self._summary_key(data.get("user_id")), "total_clicks", 1)
        await pipe.execute()

        return data["original_url"]
    
    async def get_url_stats(self, short_code: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get statistics for a shortened URL"""
        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            return None
        
        data = json.loads(link_data)
        stats = await self._ensure_stats_record(short_code, data)
        history = await self.redis.lrange(self._history_key(short_code), 0, CLICK_HISTORY_LIMIT - 1)
        owner_id = data.get("user_id")
        is_owner = user_id is not None and owner_id == user_id
        public_stats = {
            "short_code": short_code,
            "short_url": f"{self.base_url}/{short_code}",
            "clicks": int(stats.get("clicks", 0)),
        }
        if not is_owner:
            return public_stats

        return {
            "short_code": short_code,
            "original_url": data["original_url"],
            "short_url": f"{self.base_url}/{short_code}",
            "clicks": int(stats.get("clicks", 0)),
            "created_at": data["created_at"],
            "last_clicked": stats.get("last_clicked") or None,
            "click_history": history or data.get("click_history", [])
        }
    
    async def _store_link_record(self, short_code: str, link_data: Dict[str, Any]) -> bool:
        """Store one code with Redis SET NX so aliases cannot be overwritten."""
        return bool(await self.redis.set(
            f"short:{short_code}",
            json.dumps(link_data),
            ex=LINK_TTL_SECONDS,
            nx=True,
        ))

    async def _store_generated_link_record(self, link_data: Dict[str, Any]) -> str:
        """Generate and atomically reserve an available code."""
        for _ in range(5):
            short_code = generate_short_code()
            if await self._store_link_record(short_code, link_data):
                return short_code

        raise ValueError("Unable to generate a unique short code. Please try again.")

    def _url_cache_key(self, original_url: str, user_id: str = None) -> str:
        """Build the reverse lookup key scoped to anonymous or authenticated links."""
        if user_id:
            return f"url:{user_id}:{original_url}"
        return f"url:anonymous:{original_url}"

    def _owner_key(self, user_id: str = None) -> str:
        return user_id or "anonymous"

    def _links_index_key(self, user_id: str = None) -> str:
        return f"links_index:{self._owner_key(user_id)}"

    def _links_expiry_key(self, user_id: str = None) -> str:
        return f"links_expiry:{self._owner_key(user_id)}"

    def _summary_key(self, user_id: str = None) -> str:
        return f"links_summary:{self._owner_key(user_id)}"

    def _link_stats_key(self, short_code: str) -> str:
        return f"link_stats:{short_code}"

    def _history_key(self, short_code: str) -> str:
        return f"click_history:{short_code}"

    async def _ensure_stats_record(self, short_code: str, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create counters for legacy JSON records without resetting existing clicks."""
        stats_key = self._link_stats_key(short_code)
        stats = await self.redis.hgetall(stats_key)
        if stats:
            return stats

        pipe = self.redis.pipeline(transaction=True)
        pipe.hsetnx(stats_key, "clicks", int(link_data.get("clicks", 0)))
        pipe.hsetnx(stats_key, "last_clicked", link_data.get("last_clicked") or "")
        pipe.expire(stats_key, LINK_TTL_SECONDS)
        await pipe.execute()
        return await self.redis.hgetall(stats_key)

    async def _enforce_creation_quota(self, quota_key: str, user_id: str = None) -> None:
        """Apply a fixed daily quota in Redis for authenticated and anonymous callers."""
        limit = settings.USER_CREATE_LIMIT_PER_DAY if user_id else settings.ANONYMOUS_CREATE_LIMIT_PER_DAY
        window_key = f"create_quota:{quota_key}:{datetime.now(timezone.utc).date().isoformat()}"
        count = await self.redis.incr(window_key)
        if count == 1:
            await self.redis.expire(window_key, 86400)
        if count > limit:
            raise QuotaExceededError("Daily link creation limit reached")

    async def _rollback_link_creation(
        self,
        *,
        short_code: str,
        original_url: str,
        user_id: str,
        reverse_mapping: bool,
        summary_updated: bool,
    ) -> None:
        """Best-effort compensation when indexing a newly reserved link fails."""
        try:
            if reverse_mapping:
                await self._delete_reverse_mapping(original_url, short_code, user_id)
            await self.redis.delete(
                f"short:{short_code}",
                self._link_stats_key(short_code),
                self._history_key(short_code),
            )
            await self.redis.zrem(self._links_index_key(user_id), short_code)
            await self.redis.zrem(self._links_expiry_key(user_id), short_code)
            if user_id:
                await self.redis.srem(f"user_links:{user_id}", short_code)
            if summary_updated:
                await self.redis.hincrby(self._summary_key(user_id), "total_links", -1)
        except RedisError:
            # Preserve the original failure for the API's controlled error path.
            pass

    async def _delete_reverse_mapping(self, original_url: str, short_code: str, user_id: str = None) -> None:
        """Delete reverse mapping only when it points at the link being removed."""
        reverse_key = self._url_cache_key(original_url, user_id)
        existing_short_code = await self.redis.get(reverse_key)
        if existing_short_code == short_code:
            await self.redis.delete(reverse_key)

    async def _get_existing_short_code(self, original_url: str, user_id: str = None) -> Optional[str]:
        """Return a deduplicated code only when its stored owner matches."""
        reverse_key = self._url_cache_key(original_url, user_id)
        short_code = await self.redis.get(reverse_key)
        if not short_code:
            return None

        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            await self._delete_reverse_mapping(original_url, short_code, user_id)
            return None

        try:
            data = json.loads(link_data)
        except (TypeError, json.JSONDecodeError):
            await self._delete_reverse_mapping(original_url, short_code, user_id)
            return None

        if data.get("user_id") != user_id:
            # This also clears mappings written by older global-deduplication
            # versions without exposing that code to another owner.
            await self._delete_reverse_mapping(original_url, short_code, user_id)
            return None

        return short_code

    async def _rebuild_owner_index(self, user_id: str = None) -> None:
        """Backfill indexes for links written before sorted-set indexing existed."""
        if user_id:
            short_codes = await self.redis.smembers(f"user_links:{user_id}")
        else:
            short_codes = [key.replace("short:", "", 1) for key in await self.redis.keys("short:*")]
        if not short_codes:
            return

        pipe = self.redis.pipeline()
        for short_code in short_codes:
            pipe.get(f"short:{short_code}")
            pipe.hgetall(self._link_stats_key(short_code))
        records = await pipe.execute()
        total_clicks = 0
        valid_records = []
        for index, short_code in enumerate(short_codes):
            link_data = records[index * 2]
            stats = records[index * 2 + 1]
            if not link_data:
                if user_id:
                    await self.redis.srem(f"user_links:{user_id}", short_code)
                continue
            data = json.loads(link_data)
            if user_id and data.get("user_id") != user_id:
                await self.redis.srem(f"user_links:{user_id}", short_code)
                continue
            created_at = datetime.fromisoformat(data["created_at"]).timestamp()
            valid_records.append((short_code, created_at))
            total_clicks += int(stats.get("clicks", data.get("clicks", 0)))

        if valid_records:
            await self.redis.zadd(self._links_index_key(user_id), dict(valid_records))
            await self.redis.zadd(
                self._links_expiry_key(user_id),
                {short_code: created_at + LINK_TTL_SECONDS for short_code, created_at in valid_records},
            )
            await self.redis.hset(
                self._summary_key(user_id),
                mapping={"total_links": len(valid_records), "total_clicks": total_clicks},
            )

    async def _cleanup_expired_index_entries(self, user_id: str = None) -> None:
        """Remove entries whose link TTL elapsed before calculating pagination."""
        expired_codes = await self.redis.zrangebyscore(
            self._links_expiry_key(user_id),
            "-inf",
            datetime.now(timezone.utc).timestamp(),
        )
        if not expired_codes:
            return

        await self.redis.zrem(self._links_index_key(user_id), *expired_codes)
        await self.redis.zrem(self._links_expiry_key(user_id), *expired_codes)
        if user_id:
            await self.redis.srem(f"user_links:{user_id}", *expired_codes)
        await self._recalculate_owner_summary(user_id)

    async def _recalculate_owner_summary(self, user_id: str = None) -> None:
        """Rebuild summary values after expiry cleanup or legacy index repair."""
        short_codes = await self.redis.zrevrange(self._links_index_key(user_id), 0, -1)
        if not short_codes:
            await self.redis.hset(
                self._summary_key(user_id),
                mapping={"total_links": 0, "total_clicks": 0},
            )
            return

        pipe = self.redis.pipeline()
        for short_code in short_codes:
            pipe.hgetall(self._link_stats_key(short_code))
        stats_records = await pipe.execute()
        total_clicks = sum(int(stats.get("clicks", 0)) for stats in stats_records)
        await self.redis.hset(
            self._summary_key(user_id),
            mapping={"total_links": len(short_codes), "total_clicks": total_clicks},
        )

    async def get_all_links(self, skip: int = 0, limit: int = 15, user_id: str = None) -> Dict[str, Any]:
        """Get one page and dataset-wide summary values using Redis indexes."""
        await self._cleanup_expired_index_entries(user_id)
        index_key = self._links_index_key(user_id)
        total = await self.redis.zcard(index_key)
        if total == 0:
            await self._rebuild_owner_index(user_id)
            total = await self.redis.zcard(index_key)

        short_codes = await self.redis.zrevrange(index_key, skip, skip + limit - 1)
        pipe = self.redis.pipeline()
        for short_code in short_codes:
            pipe.get(f"short:{short_code}")
            pipe.hgetall(self._link_stats_key(short_code))
        records = await pipe.execute()

        links = []
        stale_codes = []
        for index, short_code in enumerate(short_codes):
            link_data = records[index * 2]
            stats = records[index * 2 + 1]
            if not link_data:
                stale_codes.append(short_code)
                continue
            data = json.loads(link_data)
            links.append({
                "short_code": short_code,
                "original_url": data["original_url"],
                "short_url": f"{self.base_url}/{short_code}",
                "clicks": int(stats.get("clicks", data.get("clicks", 0))),
                "created_at": data["created_at"]
            })
        if stale_codes:
            await self.redis.zrem(index_key, *stale_codes)
            await self.redis.zrem(self._links_expiry_key(user_id), *stale_codes)
            if user_id:
                await self.redis.srem(f"user_links:{user_id}", *stale_codes)
            await self._recalculate_owner_summary(user_id)
            total = await self.redis.zcard(index_key)

        summary = await self.redis.hgetall(self._summary_key(user_id))
        if not summary and total:
            await self._rebuild_owner_index(user_id)
            summary = await self.redis.hgetall(self._summary_key(user_id))
        total_clicks = int(summary.get("total_clicks", 0))
        return {
            "items": links,
            "total": total,
            "skip": skip,
            "limit": limit,
            "total_clicks": total_clicks,
            "average_clicks": round(total_clicks / total, 2) if total else 0.0,
        }

    async def delete_link(self, short_code: str, user_id: str = None) -> bool:
        """Delete a specific shortened link"""
        link_data = await self.redis.get(f"short:{short_code}")
        if not link_data:
            raise LinkNotFoundError(short_code)

        data = json.loads(link_data)
        owner_id = data.get("user_id")
        if user_id and owner_id != user_id:
            raise LinkOwnershipError(short_code)

        original_url = data["original_url"]
        stats = await self._ensure_stats_record(short_code, data)
        clicks = int(stats.get("clicks", 0))
        await self.redis.delete(f"short:{short_code}")
        await self.redis.delete(self._link_stats_key(short_code), self._history_key(short_code))
        await self._delete_reverse_mapping(original_url, short_code, owner_id)
        await self.redis.zrem(self._links_index_key(owner_id), short_code)
        await self.redis.zrem(self._links_expiry_key(owner_id), short_code)
        await self.redis.hincrby(self._summary_key(owner_id), "total_links", -1)
        await self.redis.hincrby(self._summary_key(owner_id), "total_clicks", -clicks)

        if owner_id:
            await self.redis.srem(f"user_links:{owner_id}", short_code)

        return True
    
    async def clear_all_links(self, user_id: str = None) -> bool:
        """Clear all shortened links"""
        if user_id:
            short_codes = await self.redis.smembers(f"user_links:{user_id}")
            for code in short_codes:
                link_data = await self.redis.get(f"short:{code}")
                if link_data:
                    data = json.loads(link_data)
                    await self._delete_reverse_mapping(data["original_url"], code, user_id)
                await self.redis.delete(
                    f"short:{code}",
                    self._link_stats_key(code),
                    self._history_key(code),
                )
            await self.redis.delete(f"user_links:{user_id}")
            await self.redis.delete(
                self._links_index_key(user_id),
                self._links_expiry_key(user_id),
                self._summary_key(user_id),
            )
        else:
            keys = await self.redis.keys("short:*")
            url_keys = await self.redis.keys("url:*")
            index_keys = await self.redis.keys("links_index:*")
            expiry_keys = await self.redis.keys("links_expiry:*")
            summary_keys = await self.redis.keys("links_summary:*")
            stats_keys = await self.redis.keys("link_stats:*")
            history_keys = await self.redis.keys("click_history:*")
            if keys:
                await self.redis.delete(*keys)
            if url_keys:
                await self.redis.delete(*url_keys)
            if index_keys:
                await self.redis.delete(*index_keys)
            if expiry_keys:
                await self.redis.delete(*expiry_keys)
            if summary_keys:
                await self.redis.delete(*summary_keys)
            if stats_keys:
                await self.redis.delete(*stats_keys)
            if history_keys:
                await self.redis.delete(*history_keys)

        return True

    async def count_links(self, user_id: str = None) -> int:
        """Count shortened links for pagination."""
        page = await self.get_all_links(skip=0, limit=1, user_id=user_id)
        return page["total"]
