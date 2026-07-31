import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from fastapi import HTTPException

from app.core.auth import get_current_user, get_optional_user
from app.core.config import settings


class AuthenticationTest(unittest.IsolatedAsyncioTestCase):
    async def test_missing_bearer_token_is_rejected(self):
        with self.assertRaisesRegex(HTTPException, "Not authenticated"):
            await get_current_user(None)

    async def test_invalid_token_is_rejected_without_auth_configuration(self):
        with patch.object(settings, "SUPABASE_URL", ""), \
                patch.object(settings, "SUPABASE_ANON_KEY", ""), \
                patch.object(settings, "SUPABASE_JWT_SECRET", ""):
            with self.assertRaisesRegex(HTTPException, "Invalid token"):
                await get_current_user("Bearer invalid-token")

    async def test_optional_auth_rejects_an_invalid_bearer_token(self):
        with patch.object(settings, "SUPABASE_URL", ""), \
                patch.object(settings, "SUPABASE_ANON_KEY", ""), \
                patch.object(settings, "SUPABASE_JWT_SECRET", ""):
            with self.assertRaisesRegex(HTTPException, "Invalid token"):
                await get_optional_user("Bearer invalid-token")

    async def test_expired_jwt_is_rejected(self):
        token = jwt.encode(
            {
                "sub": "user-1",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            "test-secret-with-at-least-thirty-two-bytes",
            algorithm="HS256",
        )
        with patch.object(settings, "SUPABASE_JWT_SECRET", "test-secret-with-at-least-thirty-two-bytes"):
            with self.assertRaisesRegex(HTTPException, "Token expired"):
                await get_current_user(f"Bearer {token}")


if __name__ == "__main__":
    unittest.main()
