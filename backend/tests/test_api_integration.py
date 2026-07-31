from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from limits import parse
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.rate_limit import create_limiter, limiter
from app.main import app
from app.services import links as links_module
from test_links_service import FakeRedis


JWT_SECRET = "test-secret-with-at-least-thirty-two-bytes"


def auth_header(user_id: str, *, expired: bool = False) -> dict[str, str]:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=5)
    if expired:
        expiration = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = jwt.encode(
        {"sub": user_id, "aud": "authenticated", "exp": expiration},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr(links_module, "redis_client", redis)
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", JWT_SECRET)
    # The integration suite isolates Redis; rate limiting is exercised separately
    # with SlowAPI's in-memory backend below.
    monkeypatch.setattr(limiter, "enabled", False)
    with TestClient(app) as test_client:
        yield test_client, redis


def test_liveness_and_readiness_endpoints(client, monkeypatch):
    test_client, _ = client

    assert test_client.get("/health/live").json() == {"status": "alive"}

    ready_redis = FakeRedis()
    async def ping():
        return True
    ready_redis.ping = ping
    monkeypatch.setattr("app.db.redis_client.redis_client", ready_redis)
    assert test_client.get("/health/ready").json()["status"] == "ready"


def test_readiness_returns_controlled_error_when_redis_is_down(client, monkeypatch):
    test_client, _ = client

    class UnavailableRedis:
        async def ping(self):
            raise RedisError("connection refused")

    monkeypatch.setattr("app.db.redis_client.redis_client", UnavailableRedis())
    response = test_client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["error_code"] == "dependency_unavailable"
    assert "connection refused" not in response.text


def test_public_shortening_rejects_invalid_destinations_and_aliases(client):
    test_client, _ = client

    valid = test_client.post("/api/v1/shorten", json={"url": "https://example.com", "custom_code": "launch"})
    assert valid.status_code == 200
    assert valid.json()["short_code"] == "launch"

    invalid_url = test_client.post("/api/v1/shorten", json={"url": "not-a-url"})
    assert invalid_url.status_code == 422

    reserved = test_client.post("/api/v1/shorten", json={"url": "https://example.com/reserved", "custom_code": "api"})
    assert reserved.status_code == 400
    assert "reserved" in reserved.json()["detail"]

    invalid_alias = test_client.post("/api/v1/shorten", json={"url": "https://example.com/invalid", "custom_code": "no spaces"})
    assert invalid_alias.status_code == 422

    duplicate = test_client.post("/api/v1/shorten", json={"url": "https://example.com/other", "custom_code": "launch"})
    assert duplicate.status_code == 409


def test_user_scoping_deduplication_and_owner_only_management(client):
    test_client, _ = client
    user_one = auth_header("user-one")
    user_two = auth_header("user-two")

    anonymous = test_client.post("/api/v1/shorten", json={"url": "https://example.com/shared"})
    first_user_one = test_client.post("/api/v1/shorten", headers=user_one, json={"url": "https://example.com/shared"})
    second_user_one = test_client.post("/api/v1/shorten", headers=user_one, json={"url": "https://example.com/shared"})
    user_two_link = test_client.post("/api/v1/shorten", headers=user_two, json={"url": "https://example.com/shared"})

    assert anonymous.status_code == first_user_one.status_code == user_two_link.status_code == 200
    assert first_user_one.json()["short_code"] == second_user_one.json()["short_code"]
    assert anonymous.json()["short_code"] != first_user_one.json()["short_code"]
    assert first_user_one.json()["short_code"] != user_two_link.json()["short_code"]

    user_one_links = test_client.get("/api/v1/admin/links", headers=user_one).json()
    user_two_links = test_client.get("/api/v1/admin/links", headers=user_two).json()
    assert user_one_links["total"] == 1
    assert user_two_links["total"] == 1

    forbidden_delete = test_client.delete(f"/api/v1/admin/links/{first_user_one.json()['short_code']}", headers=user_two)
    assert forbidden_delete.status_code == 404
    assert test_client.delete(f"/api/v1/admin/links/{first_user_one.json()['short_code']}", headers=user_one).status_code == 200

    assert test_client.get("/api/v1/admin/links", headers=user_one).json()["total"] == 0
    assert test_client.get("/api/v1/admin/links", headers=user_two).json()["total"] == 1


def test_pagination_clear_and_detailed_analytics_are_owner_scoped(client):
    test_client, _ = client
    owner = auth_header("owner")
    other_user = auth_header("other")

    first = test_client.post("/api/v1/shorten", headers=owner, json={"url": "https://example.com/one", "custom_code": "one001"})
    second = test_client.post("/api/v1/shorten", headers=owner, json={"url": "https://example.com/two", "custom_code": "two002"})
    assert first.status_code == second.status_code == 200
    assert test_client.get("/api/v1/one001").status_code == 200

    page = test_client.get("/api/v1/admin/links?skip=1&limit=1", headers=owner)
    assert page.status_code == 200
    payload = page.json()
    assert payload["total"] == 2
    assert payload["skip"] == 1
    assert payload["limit"] == 1
    assert payload["total_clicks"] == 1
    assert payload["average_clicks"] == 0.5
    assert len(payload["items"]) == 1

    public_stats = test_client.get("/api/v1/stats/one001")
    assert public_stats.status_code == 200
    assert "original_url" not in public_stats.json()
    assert "click_history" not in public_stats.json()

    other_stats = test_client.get("/api/v1/stats/one001", headers=other_user)
    assert "original_url" not in other_stats.json()
    owner_stats = test_client.get("/api/v1/stats/one001", headers=owner)
    assert owner_stats.json()["original_url"] == "https://example.com/one"
    assert owner_stats.json()["click_history"]

    assert test_client.delete("/api/v1/admin/links/clear/all", headers=owner).status_code == 200
    assert test_client.get("/api/v1/admin/links", headers=owner).json()["total"] == 0


@pytest.mark.parametrize(
    "authorization",
    [None, "Basic token", "Bearer malformed", auth_header("expired", expired=True)["Authorization"]],
)
def test_admin_endpoints_reject_missing_invalid_and_expired_tokens(client, authorization):
    test_client, _ = client
    headers = {"Authorization": authorization} if authorization else {}

    response = test_client.get("/api/v1/admin/links", headers=headers)

    assert response.status_code == 401


def test_rate_limiter_enforces_the_configured_shortening_window():
    test_limiter = create_limiter(storage_uri="memory://")
    rate = parse(settings.SHORTEN_RATE_LIMIT)

    assert all(test_limiter.limiter.hit(rate, "test-client") for _ in range(rate.amount))
    assert not test_limiter.limiter.hit(rate, "test-client")
