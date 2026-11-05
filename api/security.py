"""
API security middleware — API-key authentication and simple rate limiting.

Both features are opt-in through environment variables so local development
and the test suite keep working without configuration:

    PIPELINE_API_KEY            When set, /api/* requests must send it as
                                ``X-API-Key`` or ``Authorization: Bearer <key>``.
    API_RATE_LIMIT_PER_MINUTE   When > 0, limit requests per client IP/minute.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Paths that never require authentication or rate limiting.
_EXEMPT_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/reports",
    "/exports",
)


def is_exempt_path(path: str) -> bool:
    """Return True when a path is public (health, docs, dashboard, BI artifacts)."""
    if path == "/":
        return True
    return any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)


def is_authorized(request: Request, expected_key: str) -> bool:
    """Validate the API key from ``X-API-Key`` or a Bearer token."""
    provided = request.headers.get("x-api-key")
    if not provided:
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer":
            provided = token.strip()
    return bool(provided) and provided == expected_key


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter."""

    def __init__(self, window_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic):
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_id: str, limit: int) -> bool:
        """Record a request and return False when the limit is exceeded."""
        if limit <= 0:
            return True
        now = self._clock()
        cutoff = now - self._window
        with self._lock:
            hits = self._hits[client_id]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        """Clear all recorded hits (used by tests)."""
        with self._lock:
            self._hits.clear()


def install_security_middleware(app: FastAPI) -> SlidingWindowRateLimiter:
    """
    Attach API-key and rate-limit middleware to ``app``.

    Returns:
        The limiter instance, exposed for testing/administration.
    """
    limiter = SlidingWindowRateLimiter()
    app.state.rate_limiter = limiter

    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        if not is_exempt_path(request.url.path):
            expected_key = os.getenv("PIPELINE_API_KEY", "")
            if expected_key and not is_authorized(request, expected_key):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API key"},
                )

            try:
                limit = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "0") or "0")
            except ValueError:
                limit = 0

            if limit > 0:
                client_id = request.client.host if request.client else "unknown"
                if not limiter.allow(client_id, limit):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Try again later."},
                    )

        return await call_next(request)

    return limiter
