"""Liveness/readiness checks for the API and its dependencies."""
from __future__ import annotations

import redis
from fastapi import APIRouter

from ...config import get_settings
from ...db import connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness — the process is up."""
    return {"status": "ok", "service": "triage-api"}


@router.get("/health/ready")
def readiness() -> dict:
    """Readiness — Postgres and Redis are reachable."""
    checks: dict[str, str] = {}

    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"

    try:
        client = redis.from_url(get_settings().redis_url)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    healthy = all(v == "ok" for v in checks.values())
    return {"status": "ok" if healthy else "degraded", "checks": checks}
