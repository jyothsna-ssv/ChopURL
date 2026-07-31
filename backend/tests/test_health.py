import unittest
from unittest.mock import AsyncMock, patch

from app.main import health_check, liveness_check, ready_health_check


class HealthEndpointTest(unittest.IsolatedAsyncioTestCase):
    async def test_liveness_does_not_require_dependencies(self):
        self.assertEqual(await liveness_check(), {"status": "alive"})

    async def test_readiness_checks_redis_connectivity(self):
        redis = AsyncMock()
        with patch("app.db.redis_client.redis_client", redis):
            result = await health_check()

        redis.ping.assert_awaited_once()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["checks"]["redis"], "ok")

    async def test_ready_endpoint_uses_the_same_redis_check(self):
        redis = AsyncMock()
        with patch("app.db.redis_client.redis_client", redis):
            result = await ready_health_check()

        redis.ping.assert_awaited_once()
        self.assertEqual(result["status"], "ready")


if __name__ == "__main__":
    unittest.main()
