"""Analytics aggregates and audit-log surfacing (Module 8).

All queries are org-scoped and bounded to a rolling window. Metrics map to the
PRD success metrics: volume, category mix, first-response time, hours saved, and
draft acceptance (drafts sent with no edit)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context
from ...config import get_settings
from ...db import connection

router = APIRouter(tags=["analytics"])


class Summary(BaseModel):
    emails_processed: int
    median_response_seconds: float | None
    hours_saved: float
    draft_acceptance_rate: float | None
    llm_tokens: int = 0
    failed_jobs: int = 0


class VolumePoint(BaseModel):
    date: str
    ai_handled: int
    human_required: int


class CategorySlice(BaseModel):
    category: str
    count: int
    pct: float


class AnalyticsResponse(BaseModel):
    range_days: int
    summary: Summary
    volume: list[VolumePoint]
    category_mix: list[CategorySlice]


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(ctx: AuthContext = Depends(get_auth_context), days: int = Query(default=30, ge=1, le=365)) -> AnalyticsResponse:
    org = ctx.organization_id
    window = f"now() - interval '{int(days)} days'"

    with connection() as conn:
        emails_processed = conn.execute(
            f"SELECT count(*) AS n FROM emails WHERE organization_id=%s AND deleted_at IS NULL AND created_at >= {window}",
            (org,),
        ).fetchone()["n"]

        median = conn.execute(
            f"""
            SELECT percentile_cont(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (d.sent_at - COALESCE(e.received_at, e.created_at)))
            ) AS med
            FROM drafts d JOIN emails e ON e.id = d.email_id
            WHERE d.organization_id=%s AND d.status='sent' AND d.sent_at IS NOT NULL
              AND d.sent_at >= {window}
            """,
            (org,),
        ).fetchone()["med"]

        accept = conn.execute(
            f"""
            SELECT count(*) FILTER (WHERE was_edited = false) AS unedited, count(*) AS total
            FROM drafts WHERE organization_id=%s AND status='sent' AND sent_at >= {window}
            """,
            (org,),
        ).fetchone()

        handled = conn.execute(
            f"""SELECT count(*) AS n FROM emails WHERE organization_id=%s AND deleted_at IS NULL
                AND status IN ('drafted','sent') AND created_at >= {window}""",
            (org,),
        ).fetchone()["n"]

        volume_rows = conn.execute(
            f"""
            SELECT to_char(date_trunc('day', created_at), 'YYYY-MM-DD') AS day,
                   count(*) FILTER (WHERE status IN ('drafted','sent')) AS ai_handled,
                   count(*) FILTER (WHERE status = 'review') AS human_required
            FROM emails
            WHERE organization_id=%s AND deleted_at IS NULL AND created_at >= {window}
            GROUP BY day ORDER BY day
            """,
            (org,),
        ).fetchall()

        cat_rows = conn.execute(
            f"""
            SELECT c.category, count(*) AS n
            FROM classifications c JOIN emails e ON e.id = c.email_id AND e.deleted_at IS NULL
            WHERE c.organization_id=%s AND c.deleted_at IS NULL AND c.created_at >= {window}
            GROUP BY c.category ORDER BY n DESC
            """,
            (org,),
        ).fetchall()

        tokens = conn.execute(
            f"SELECT COALESCE(SUM(prompt_tokens + completion_tokens), 0) AS t FROM llm_usage "
            f"WHERE organization_id=%s AND created_at >= {window}",
            (org,),
        ).fetchone()["t"]

        failed = conn.execute(
            f"SELECT count(*) AS n FROM jobs WHERE organization_id=%s AND status='failed' AND created_at >= {window}",
            (org,),
        ).fetchone()["n"]

    minutes = get_settings().minutes_saved_per_email
    cat_total = sum(r["n"] for r in cat_rows) or 1
    acceptance = (accept["unedited"] / accept["total"]) if accept and accept["total"] else None

    return AnalyticsResponse(
        range_days=days,
        summary=Summary(
            emails_processed=int(emails_processed),
            median_response_seconds=float(median) if median is not None else None,
            hours_saved=round(handled * minutes / 60.0, 1),
            draft_acceptance_rate=round(acceptance, 3) if acceptance is not None else None,
            llm_tokens=int(tokens),
            failed_jobs=int(failed),
        ),
        volume=[VolumePoint(date=r["day"], ai_handled=r["ai_handled"], human_required=r["human_required"]) for r in volume_rows],
        category_mix=[CategorySlice(category=r["category"], count=r["n"], pct=round(r["n"] / cat_total, 3)) for r in cat_rows],
    )


class AuditEntry(BaseModel):
    id: str
    actor_email: str | None
    action: str
    entity: dict
    created_at: str | None


@router.get("/audit", response_model=list[AuditEntry])
def audit(ctx: AuthContext = Depends(get_auth_context), limit: int = Query(default=50, le=200), offset: int = 0) -> list[AuditEntry]:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.action, a.entity, a.created_at, u.email AS actor_email
            FROM audit_logs a LEFT JOIN users u ON u.id = a.actor_id
            WHERE a.organization_id=%s AND a.deleted_at IS NULL
            ORDER BY a.created_at DESC LIMIT %s OFFSET %s
            """,
            (ctx.organization_id, limit, offset),
        ).fetchall()
    return [
        AuditEntry(id=str(r["id"]), actor_email=r["actor_email"], action=r["action"],
                   entity=r["entity"] or {}, created_at=r["created_at"].isoformat() if r["created_at"] else None)
        for r in rows
    ]
