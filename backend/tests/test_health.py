import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.core.config import settings
from app.main import health_check, liveness_check


class HealthEndpointTest(unittest.IsolatedAsyncioTestCase):
    async def test_liveness_does_not_require_dependencies(self):
        self.assertEqual(await liveness_check(), {"status": "alive"})

    async def test_readiness_checks_redis_and_auth_configuration(self):
        redis = AsyncMock()
        with patch("app.db.redis_client.redis_client", redis), \
                patch.object(settings, "SUPABASE_URL", "https://project.supabase.co"), \
                patch.object(settings, "SUPABASE_ANON_KEY", "public-key"):
            result = await health_check()

        redis.ping.assert_awaited_once()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["checks"]["redis"], "ok")

    async def test_readiness_rejects_missing_auth_configuration(self):
        redis = AsyncMock()
        with patch("app.db.redis_client.redis_client", redis), \
                patch.object(settings, "SUPABASE_URL", ""), \
                patch.object(settings, "SUPABASE_ANON_KEY", ""):
            with self.assertRaisesRegex(HTTPException, "not configured"):
                await health_check()


if __name__ == "__main__":
    unittest.main()
