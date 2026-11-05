"""
Unit Tests: API Security

Covers opt-in API-key authentication and the in-memory rate limiter.
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.main import app
from api.security import (
    SlidingWindowRateLimiter,
    is_authorized,
    is_exempt_path,
)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class TestPathExemptions:
    def test_public_paths(self):
        assert is_exempt_path("/")
        assert is_exempt_path("/health")
        assert is_exempt_path("/docs")
        assert is_exempt_path("/openapi.json")

    def test_protected_paths(self):
        assert not is_exempt_path("/api/v1/pipelines")
        assert not is_exempt_path("/api/v1/quality/metrics")


class TestRateLimiter:
    def test_allows_up_to_limit(self):
        clock = FakeClock()
        limiter = SlidingWindowRateLimiter(clock=clock)
        assert limiter.allow("client", 2)
        assert limiter.allow("client", 2)
        assert not limiter.allow("client", 2)

    def test_window_slides(self):
        clock = FakeClock()
        limiter = SlidingWindowRateLimiter(window_seconds=60, clock=clock)
        assert limiter.allow("client", 1)
        assert not limiter.allow("client", 1)
        clock.now += 61
        assert limiter.allow("client", 1)

    def test_separate_clients(self):
        limiter = SlidingWindowRateLimiter()
        assert limiter.allow("a", 1)
        assert limiter.allow("b", 1)

    def test_non_positive_limit_disables(self):
        limiter = SlidingWindowRateLimiter()
        assert limiter.allow("client", 0)
        assert limiter.allow("client", -1)

    def test_reset(self):
        clock = FakeClock()
        limiter = SlidingWindowRateLimiter(clock=clock)
        assert limiter.allow("client", 1)
        assert not limiter.allow("client", 1)
        limiter.reset()
        assert limiter.allow("client", 1)


class TestApiKeyMiddleware:
    def test_health_is_public_even_with_key(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_API_KEY", "secret")
        client = TestClient(app)
        assert client.get("/health").status_code == 200

    def test_missing_key_is_rejected(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_API_KEY", "secret")
        client = TestClient(app)
        response = client.get("/api/v1/pipelines")
        assert response.status_code == 401

    def test_x_api_key_is_accepted(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_API_KEY", "secret")
        client = TestClient(app)
        response = client.get("/api/v1/pipelines", headers={"X-API-Key": "secret"})
        assert response.status_code == 200

    def test_bearer_token_is_accepted(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_API_KEY", "secret")
        client = TestClient(app)
        response = client.get(
            "/api/v1/pipelines",
            headers={"Authorization": "Bearer secret"},
        )
        assert response.status_code == 200

    def test_wrong_key_is_rejected(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_API_KEY", "secret")
        client = TestClient(app)
        response = client.get("/api/v1/pipelines", headers={"X-API-Key": "nope"})
        assert response.status_code == 401

    def test_is_authorized_helper(self):
        class Request:
            def __init__(self, headers):
                self.headers = headers

        assert is_authorized(Request({"x-api-key": "abc"}), "abc")
        assert is_authorized(Request({"authorization": "Bearer abc"}), "abc")
        assert not is_authorized(Request({}), "abc")


class TestRateLimitMiddleware:
    def test_rate_limit_returns_429(self, monkeypatch):
        monkeypatch.delenv("PIPELINE_API_KEY", raising=False)
        monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "1")
        app.state.rate_limiter.reset()
        client = TestClient(app)

        assert client.get("/api/v1/pipelines").status_code == 200
        assert client.get("/api/v1/pipelines").status_code == 429
        # Health checks remain exempt.
        assert client.get("/health").status_code == 200

    def test_rate_limit_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("PIPELINE_API_KEY", raising=False)
        monkeypatch.delenv("API_RATE_LIMIT_PER_MINUTE", raising=False)
        app.state.rate_limiter.reset()
        client = TestClient(app)

        for _ in range(3):
            assert client.get("/api/v1/pipelines").status_code == 200
