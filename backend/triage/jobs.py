"""Helpers for the `jobs` table — the durable record of background work.

Every queued task should create a job row, then transition it through
running → succeeded/failed so progress and failures are observable and
poison jobs can be dead-lettered (TRD reliability conventions).
"""
from __future__ import annotations

import json
from typing import Any

from .db import connection
from .logging import get_logger

log = get_logger(__name__)


def create_job(kind: str, *, organization_id: str | None = None, payload: dict | None = None) -> str:
    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO jobs (organization_id, kind, status, payload)
            VALUES (%s, %s, 'queued', %s) RETURNING id
            """,
            (organization_id, kind, json.dumps(payload or {})),
        ).fetchone()
    return str(row["id"])


def mark_running(job_id: str, task_id: str | None = None) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'running', started_at = now(),
                attempts = attempts + 1, task_id = COALESCE(%s, task_id)
            WHERE id = %s
            """,
            (task_id, job_id),
        )


def update_progress(job_id: str, progress: float) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE jobs SET progress = %s WHERE id = %s",
            (max(0.0, min(1.0, progress)), job_id),
        )


def mark_succeeded(job_id: str, result: dict[str, Any] | None = None) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'succeeded', progress = 1, finished_at = now(), result = %s, error = NULL
            WHERE id = %s
            """,
            (json.dumps(result or {}), job_id),
        )


def mark_failed(job_id: str, error: str) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'failed', finished_at = now(), error = %s
            WHERE id = %s
            """,
            (error[:4000], job_id),
        )
    log.error("job_failed", job_id=job_id, error=error[:500])
