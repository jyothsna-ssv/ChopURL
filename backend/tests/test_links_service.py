import fnmatch
import asyncio
import unittest
from unittest.mock import patch

from app.core.config import settings
from app.core.errors import LinkOwnershipError
from app.services.links import LINK_TTL_SECONDS, LinkService, QuotaExceededError


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}
        self.sorted_sets = {}
        self.hashes = {}
        self.lists = {}
        self.expirations = {}
        self.set_calls = []

    async def get(self, key):
        return self.values.get(key)

    async def setex(self, key, ttl, value):
        self.values[key] = value
        self.expirations[key] = ttl

    async def set(self, key, value, ex=None, nx=False):
        self.set_calls.append({"key": key, "ex": ex, "nx": nx})
        if nx and key in self.values:
            return False
        self.values[key] = value
        if ex:
            self.expirations[key] = ex
        return True

    async def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    async def expire(self, key, ttl):
        self.expirations[key] = ttl
        return True

    async def sadd(self, key, *values):
        self.sets.setdefault(key, set()).update(values)

    async def smembers(self, key):
        return set(self.sets.get(key, set()))

    async def srem(self, key, *values):
        for value in values:
            self.sets.setdefault(key, set()).discard(value)

    async def zadd(self, key, mapping):
        self.sorted_sets.setdefault(key, {}).update(mapping)

    async def zcard(self, key):
        return len(self.sorted_sets.get(key, {}))

    async def zrevrange(self, key, start, end):
        entries = sorted(
            self.sorted_sets.get(key, {}).items(),
            key=lambda item: (-item[1], item[0]),
        )
        if end == -1:
            entries = entries[start:]
        else:
            entries = entries[start:end + 1]
        return [code for code, _ in entries]

    async def zrangebyscore(self, key, minimum, maximum):
        minimum = float("-inf") if minimum == "-inf" else float(minimum)
        maximum = float("inf") if maximum == "+inf" else float(maximum)
        return [
            code
            for code, score in self.sorted_sets.get(key, {}).items()
            if minimum <= score <= maximum
        ]

    async def zrem(self, key, *values):
        entries = self.sorted_sets.setdefault(key, {})
        for value in values:
            entries.pop(value, None)

    async def hincrby(self, key, field, amount):
        bucket = self.hashes.setdefault(key, {})
        bucket[field] = int(bucket.get(field, 0)) + amount
        return bucket[field]

    async def hsetnx(self, key, field, value):
        if field not in self.hashes.setdefault(key, {}):
            self.hashes[key][field] = value
            return 1
        return 0

    async def hset(self, key, field=None, value=None, mapping=None, **kwargs):
        values = mapping or kwargs
        if field is not None:
            values = {field: value}
        self.hashes.setdefault(key, {}).update(values)

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def lpush(self, key, *values):
        entries = self.lists.setdefault(key, [])
        for value in values:
            entries.insert(0, value)
        return len(entries)

    async def ltrim(self, key, start, end):
        self.lists[key] = self.lists.get(key, [])[start:end + 1]

    async def lrange(self, key, start, end):
        return list(self.lists.get(key, [])[start:end + 1])

    def pipeline(self, *args, **kwargs):
        return FakePipeline(self)

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.sets.pop(key, None)
            self.sorted_sets.pop(key, None)
            self.hashes.pop(key, None)
            self.lists.pop(key, None)
            self.expirations.pop(key, None)

    async def keys(self, pattern):
        return [
            key
            for key in set(self.values) | set(self.sets) | set(self.sorted_sets) | set(self.hashes) | set(self.lists)
            if fnmatch.fnmatch(key, pattern)
        ]


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.operations = []

    def _queue(self, method, *args, **kwargs):
        self.operations.append((method, args, kwargs))
        return self

    def get(self, key):
        return self._queue("get", key)

    def hgetall(self, key):
        return self._queue("hgetall", key)

    def hincrby(self, key, field, amount):
        return self._queue("hincrby", key, field, amount)

    def hset(self, key, field, value):
        return self._queue("hset", key, field, value)

    def hsetnx(self, key, field, value):
        return self._queue("hsetnx", key, field, value)

    def lpush(self, key, value):
        return self._queue("lpush", key, value)

    def ltrim(self, key, start, end):
        return self._queue("ltrim", key, start, end)

    def expire(self, key, ttl):
        return self._queue("expire", key, ttl)

    def zadd(self, key, mapping):
        return self._queue("zadd", key, mapping)

    async def execute(self):
        results = []
        for method, args, kwargs in self.operations:
            results.append(await getattr(self.redis, method)(*args, **kwargs))
        return results


class YieldingFakeRedis(FakeRedis):
    async def get(self, key):
        await asyncio.sleep(0)
        return await super().get(key)


class LinkServiceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = LinkService()
        self.service.redis = FakeRedis()
        self.service.base_url = "http://testserver"

    async def test_reserved_custom_codes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "reserved"):
            await self.service.create_short_url("https://example.com", "health")

    async def test_invalid_custom_codes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "3-32 characters"):
            await self.service.create_short_url("https://example.com", "no spaces")

    async def test_private_destinations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Private or reserved"):
            await self.service.create_short_url("http://127.0.0.1/internal")

    async def test_creation_quota_is_enforced_in_redis(self):
        with patch.object(settings, "ANONYMOUS_CREATE_LIMIT_PER_DAY", 1):
            await self.service.create_short_url(
                "https://example.com/one",
                "quota01",
                quota_key="ip:127.0.0.1",
            )

            with self.assertRaises(QuotaExceededError):
                await self.service.create_short_url(
                    "https://example.com/two",
                    "quota02",
                    quota_key="ip:127.0.0.1",
                )

    async def test_duplicate_custom_codes_are_rejected(self):
        await self.service.create_short_url("https://example.com/one", " Launch ")

        with self.assertRaisesRegex(ValueError, "already exists"):
            await self.service.create_short_url("https://example.com/two", "LAUNCH")

        self.assertIsNotNone(await self.service.redis.get("short:launch"))
        self.assertTrue(any(call["nx"] for call in self.service.redis.set_calls))

    async def test_duplicate_alias_does_not_consume_creation_quota(self):
        with patch.object(settings, "ANONYMOUS_CREATE_LIMIT_PER_DAY", 1):
            await self.service.create_short_url(
                "https://example.com/one",
                "quota01",
                quota_key="ip:127.0.0.1",
            )

            with self.assertRaisesRegex(ValueError, "already exists"):
                await self.service.create_short_url(
                    "https://example.com/two",
                    "quota01",
                    quota_key="ip:127.0.0.1",
                )

        quota_values = [
            value
            for key, value in self.service.redis.values.items()
            if key.startswith("create_quota:ip:127.0.0.1:")
        ]
        self.assertEqual(quota_values, [1])

    async def test_link_records_and_stats_share_the_one_year_ttl(self):
        await self.service.create_short_url("https://example.com", "ttl001", user_id="user-1")

        self.assertEqual(self.service.redis.expirations["short:ttl001"], LINK_TTL_SECONDS)
        self.assertEqual(self.service.redis.expirations["link_stats:ttl001"], LINK_TTL_SECONDS)

        await self.service.get_original_url("ttl001")

        self.assertEqual(self.service.redis.expirations["click_history:ttl001"], LINK_TTL_SECONDS)

    async def test_random_code_generation_retries_collisions(self):
        await self.service.redis.setex("short:first1", 31536000, "{}")

        with patch("app.services.links.generate_short_code", side_effect=["first1", "second2"]):
            short_url = await self.service.create_short_url("https://example.com")

        self.assertEqual(short_url, "http://testserver/second2")

    async def test_deduplicates_links_within_same_owner_context(self):
        with patch("app.services.links.generate_short_code", side_effect=["anon01", "user01", "user02"]):
            anonymous_url = await self.service.create_short_url("https://example.com")
            duplicate_anonymous_url = await self.service.create_short_url("https://example.com")
            first_user_url = await self.service.create_short_url("https://example.com", user_id="user-1")
            second_user_url = await self.service.create_short_url("https://example.com", user_id="user-2")
            duplicate_first_user_url = await self.service.create_short_url("https://example.com", user_id="user-1")

        self.assertEqual(anonymous_url, duplicate_anonymous_url)
        self.assertEqual(anonymous_url, "http://testserver/anon01")
        self.assertEqual(first_user_url, duplicate_first_user_url)
        self.assertEqual(first_user_url, "http://testserver/user01")
        self.assertEqual(second_user_url, "http://testserver/user02")
        self.assertEqual(await self.service.count_links("user-1"), 1)
        self.assertEqual(await self.service.count_links("user-2"), 1)

    async def test_stale_mapping_cannot_cross_owner_boundaries(self):
        await self.service.redis.setex("url:user-2:https://example.com", 31536000, "foreign")
        await self.service.redis.setex(
            "short:foreign",
            31536000,
            '{"original_url":"https://example.com","user_id":"user-1","clicks":0,"created_at":"2024-01-01T00:00:00+00:00"}',
        )

        with patch("app.services.links.generate_short_code", return_value="owned1"):
            short_url = await self.service.create_short_url("https://example.com", user_id="user-2")

        self.assertEqual(short_url, "http://testserver/owned1")
        self.assertEqual(await self.service.count_links("user-2"), 1)

    async def test_redirect_updates_click_stats(self):
        await self.service.create_short_url("https://example.com", "promo", user_id="user-1")

        first_redirect = await self.service.get_original_url("promo")
        second_redirect = await self.service.get_original_url("promo")
        stats = await self.service.get_url_stats("promo", user_id="user-1")

        self.assertEqual(first_redirect, "https://example.com")
        self.assertEqual(second_redirect, "https://example.com")
        self.assertEqual(stats["clicks"], 2)
        self.assertIsNotNone(stats["last_clicked"])
        self.assertEqual(len(stats["click_history"]), 2)

        public_stats = await self.service.get_url_stats("promo")
        self.assertEqual(public_stats["clicks"], 2)
        self.assertNotIn("original_url", public_stats)
        self.assertNotIn("click_history", public_stats)

    async def test_concurrent_redirects_increment_clicks_atomically(self):
        self.service.redis = YieldingFakeRedis()
        await self.service.create_short_url("https://example.com", "atomic1", user_id="user-1")

        await asyncio.gather(*[
            self.service.get_original_url("atomic1")
            for _ in range(25)
        ])

        stats = await self.service.get_url_stats("atomic1", user_id="user-1")
        page = await self.service.get_all_links(user_id="user-1")

        self.assertEqual(stats["clicks"], 25)
        self.assertEqual(len(stats["click_history"]), 25)
        self.assertEqual(page["total_clicks"], 25)

    async def test_admin_delete_is_owner_scoped(self):
        await self.service.create_short_url("https://example.com", "mine", user_id="user-1")

        with self.assertRaises(LinkOwnershipError):
            await self.service.delete_link("mine", user_id="user-2")
        self.assertEqual(await self.service.count_links("user-1"), 1)

        self.assertTrue(await self.service.delete_link("mine", user_id="user-1"))
        self.assertEqual(await self.service.count_links("user-1"), 0)

    async def test_count_links_removes_stale_user_set_members(self):
        await self.service.redis.sadd("user_links:user-1", "expired")

        self.assertEqual(await self.service.count_links("user-1"), 0)
        self.assertEqual(await self.service.redis.smembers("user_links:user-1"), set())

    async def test_paginated_response_includes_dataset_summary(self):
        await self.service.create_short_url("https://example.com/one", "one001", user_id="user-1")
        await self.service.create_short_url("https://example.com/two", "two002", user_id="user-1")
        await self.service.get_original_url("one001")
        await self.service.get_original_url("one001")
        await self.service.get_original_url("two002")

        page = await self.service.get_all_links(skip=1, limit=1, user_id="user-1")

        self.assertEqual(page["total"], 2)
        self.assertEqual(page["skip"], 1)
        self.assertEqual(page["limit"], 1)
        self.assertEqual(page["total_clicks"], 3)
        self.assertEqual(page["average_clicks"], 1.5)
        self.assertEqual(len(page["items"]), 1)

    async def test_expired_index_entries_are_removed_before_pagination(self):
        await self.service.create_short_url("https://example.com", "expired1", user_id="user-1")
        await self.service.redis.zadd(self.service._links_expiry_key("user-1"), {"expired1": 0})

        page = await self.service.get_all_links(user_id="user-1")

        self.assertEqual(page["total"], 0)
        self.assertEqual(page["items"], [])

    async def test_deleting_custom_link_keeps_anonymous_reverse_mapping(self):
        with patch("app.services.links.generate_short_code", return_value="anon01"):
            anonymous_url = await self.service.create_short_url("https://example.com")

        await self.service.create_short_url("https://example.com", "brand", user_id="user-1")
        await self.service.delete_link("brand", user_id="user-1")

        duplicate_anonymous_url = await self.service.create_short_url("https://example.com")

        self.assertEqual(anonymous_url, duplicate_anonymous_url)


if __name__ == "__main__":
    unittest.main()
