import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from starlette.requests import Request

from app.api.routers import shorten_url
from app.core.errors import ShortCodeConflictError, ShortCodeGenerationError
from app.models.schemas import URLRequest


class ShortenRouteTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.request = Request({
            "type": "http",
            "method": "POST",
            "path": "/api/v1/shorten",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        })
        self.payload = URLRequest(url="https://example.com", custom_code="launch")

    async def test_custom_code_collision_returns_conflict(self):
        with patch("app.api.routers.LinkService") as service_class:
            service_class.return_value.create_short_url = AsyncMock(
                side_effect=ShortCodeConflictError("launch")
            )
            with self.assertRaises(HTTPException) as context:
                await shorten_url.__wrapped__(self.request, self.payload, user_id=None)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "Custom code is already in use")

    async def test_generated_code_exhaustion_returns_controlled_service_error(self):
        with patch("app.api.routers.LinkService") as service_class:
            service_class.return_value.create_short_url = AsyncMock(
                side_effect=ShortCodeGenerationError("internal collision detail")
            )
            with self.assertRaises(HTTPException) as context:
                await shorten_url.__wrapped__(self.request, self.payload, user_id=None)

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail, "Unable to allocate a short code. Please try again.")


if __name__ == "__main__":
    unittest.main()
