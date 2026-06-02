"""Per-tenant rate limiting (TRD scalability: one customer can't starve others).

A fixed-window counter in Redis keyed by organisation + bucket. Used as a
FastAPI dependency on expensive endpoints (LLM calls, uploads, ingestion). Fails
open if Redis is unavailable — rate limiting should never take the API down.
"""
from __future__ import annotations

import time

import redis
from fastapi import Depends, HTTPException, status

from ..config import get_settings
from ..logging import get_logger
from ..auth import AuthContext, get_auth_context

log = get_logger(__name__)

_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(get_settings().redis_url)
    return _client


def rate_limit(bucket: str, limit: int, window_seconds: int = 60):
    """Build a dependency enforcing `limit` requests per `window_seconds` per org."""

    def dependency(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        window = int(time.time()) // window_seconds
        key = f"rl:{bucket}:{ctx.organization_id}:{window}"
        try:
            client = _redis()
            count = client.incr(key)
            if count == 1:
                client.expire(key, window_seconds)
        except Exception as exc:  # fail open
            log.warning("rate_limit_unavailable", error=str(exc))
            return ctx
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for '{bucket}'. Try again shortly.",
                headers={"Retry-After": str(window_seconds)},
            )
        return ctx

    return dependency
