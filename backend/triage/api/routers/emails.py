"""Email-centric endpoints. Module 3 adds re-classification; the triage queue
list/detail endpoints arrive with the Review UI (Module 7)."""
from __future__ import annotations

import json as _json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context
from ...db import OrgScopedDb, connection
from ..ratelimit import rate_limit
from ... import jobs

router = APIRouter(prefix="/emails", tags=["emails"])


# ── Triage queue list ──────────────────────────────────────────────────────
class QueueItem(BaseModel):
    id: str
    from_address: str
    subject: str | None
    status: str
    category: str | None = None
    confidence: float | None = None
    urgency: str | None = None
    assignee_id: str | None = None
    assignee_name: str | None = None
    has_draft: bool = False
    received_at: str | None = None


class QueueResponse(BaseModel):
    items: list[QueueItem]
    total: int
    limit: int
    offset: int


@router.get("", response_model=QueueResponse)
def list_emails(
    ctx: AuthContext = Depends(get_auth_context),
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    mine: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
) -> QueueResponse:
    """Paginated triage queue with filters (status/category/urgency/assignee/search)."""
    where = ["e.organization_id = %s", "e.deleted_at IS NULL"]
    params: list = [ctx.organization_id]
    if status:
        where.append("e.status = %s"); params.append(status)
    if category:
        where.append("c.category = %s"); params.append(category)
    if urgency:
        where.append("c.urgency = %s"); params.append(urgency)
    if mine:
        where.append("e.assignee_id = %s"); params.append(ctx.user_id)
    elif assignee_id:
        where.append("e.assignee_id = %s"); params.append(assignee_id)
    if q:
        where.append("(e.subject ILIKE %s OR e.from_address ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    where_sql = " AND ".join(where)

    base_from = (
        "FROM emails e "
        "LEFT JOIN classifications c ON c.email_id = e.id AND c.deleted_at IS NULL "
        "LEFT JOIN users u ON u.id = e.assignee_id "
    )
    with connection() as conn:
        total = conn.execute(f"SELECT count(*) AS n FROM emails e "
                             f"LEFT JOIN classifications c ON c.email_id=e.id AND c.deleted_at IS NULL "
                             f"WHERE {where_sql}", params).fetchone()["n"]
        rows = conn.execute(
            f"SELECT e.id, e.from_address, e.subject, e.status, e.received_at, e.assignee_id, "
            f"c.category, c.confidence, c.urgency, COALESCE(u.full_name, u.email) AS assignee_name, "
            f"EXISTS(SELECT 1 FROM drafts d WHERE d.email_id=e.id AND d.deleted_at IS NULL) AS has_draft "
            f"{base_from} WHERE {where_sql} "
            f"ORDER BY e.received_at DESC NULLS LAST, e.created_at DESC LIMIT %s OFFSET %s",
            params + [limit, offset],
        ).fetchall()

    items = [
        QueueItem(
            id=str(r["id"]), from_address=r["from_address"], subject=r["subject"], status=r["status"],
            category=r["category"], confidence=float(r["confidence"]) if r["confidence"] is not None else None,
            urgency=r["urgency"], assignee_id=str(r["assignee_id"]) if r["assignee_id"] else None,
            assignee_name=r["assignee_name"], has_draft=r["has_draft"],
            received_at=r["received_at"].isoformat() if r["received_at"] else None,
        )
        for r in rows
    ]
    return QueueResponse(items=items, total=int(total), limit=limit, offset=offset)


# ── Email detail ────────────────────────────────────────────────────────────
class EmailDetail(BaseModel):
    id: str
    from_address: str
    to_address: str | None
    subject: str | None
    body_clean: str | None
    status: str
    received_at: str | None
    assignee_id: str | None
    classification: dict | None = None
    draft: dict | None = None
    thread: list[dict] = []


@router.get("/{email_id}", response_model=EmailDetail)
def get_email(email_id: str, ctx: AuthContext = Depends(get_auth_context)) -> EmailDetail:
    """Email + classification + current draft (with citations) + thread messages."""
    with connection() as conn:
        e = conn.execute(
            "SELECT * FROM emails WHERE id=%s AND organization_id=%s AND deleted_at IS NULL",
            (email_id, ctx.organization_id),
        ).fetchone()
        if not e:
            raise HTTPException(status_code=404, detail="Email not found")
        cls = conn.execute(
            "SELECT category, confidence, urgency, rationale, model FROM classifications "
            "WHERE email_id=%s AND deleted_at IS NULL", (email_id,),
        ).fetchone()
        draft = conn.execute(
            "SELECT id, body, status, sources, model FROM drafts "
            "WHERE email_id=%s AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 1", (email_id,),
        ).fetchone()
        thread = []
        if e["thread_id"]:
            thread = conn.execute(
                "SELECT from_address, subject, body_clean, received_at FROM emails "
                "WHERE organization_id=%s AND thread_id=%s AND deleted_at IS NULL "
                "ORDER BY received_at ASC NULLS FIRST", (ctx.organization_id, e["thread_id"]),
            ).fetchall()

    return EmailDetail(
        id=str(e["id"]), from_address=e["from_address"], to_address=e["to_address"], subject=e["subject"],
        body_clean=e["body_clean"], status=e["status"],
        received_at=e["received_at"].isoformat() if e["received_at"] else None,
        assignee_id=str(e["assignee_id"]) if e["assignee_id"] else None,
        classification=(dict(cls) | {"confidence": float(cls["confidence"])}) if cls else None,
        draft=({"id": str(draft["id"]), "body": draft["body"], "status": draft["status"],
                "sources": draft["sources"] or [], "model": draft["model"]} if draft else None),
        thread=[{"from_address": m["from_address"], "subject": m["subject"],
                 "body_clean": m["body_clean"],
                 "received_at": m["received_at"].isoformat() if m["received_at"] else None} for m in thread],
    )


class ClassifyResponse(BaseModel):
    job_id: str
    email_id: str


@router.post("/{email_id}/classify", response_model=ClassifyResponse)
def reclassify(email_id: str, ctx: AuthContext = Depends(get_auth_context),
               _rl: AuthContext = Depends(rate_limit("classify", 60))) -> ClassifyResponse:
    """Re-run classification for an email (e.g. after a prompt/model change)."""
    if not OrgScopedDb(ctx.organization_id).fetch_one("emails", {"id": email_id}):
        raise HTTPException(status_code=404, detail="Email not found")

    from ...worker.tasks import classify_email

    job_id = jobs.create_job("classify", organization_id=ctx.organization_id,
                             payload={"email_id": email_id, "reclassify": True})
    classify_email.apply_async(kwargs={"job_id": job_id, "email_id": email_id,
                                       "organization_id": ctx.organization_id})
    return ClassifyResponse(job_id=job_id, email_id=email_id)


# ── Drafting (Module 5) ────────────────────────────────────────────────────
class DraftOut(BaseModel):
    draft_id: str | None
    body: str | None
    status: str | None
    sources: list[dict] = []
    model: str | None = None


@router.get("/{email_id}/draft", response_model=DraftOut)
def get_draft(email_id: str, ctx: AuthContext = Depends(get_auth_context)) -> DraftOut:
    """Return the current (editable or sent) draft for an email, with citations."""
    if not OrgScopedDb(ctx.organization_id).fetch_one("emails", {"id": email_id}):
        raise HTTPException(status_code=404, detail="Email not found")
    with connection() as conn:
        row = conn.execute(
            "SELECT id, body, status, sources, model FROM drafts "
            "WHERE email_id = %s AND organization_id = %s AND deleted_at IS NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (email_id, ctx.organization_id),
        ).fetchone()
    if not row:
        return DraftOut(draft_id=None, body=None, status=None, sources=[])
    return DraftOut(draft_id=str(row["id"]), body=row["body"], status=row["status"],
                    sources=row.get("sources") or [], model=row.get("model"))


class RegenResponse(BaseModel):
    job_id: str
    email_id: str


@router.post("/{email_id}/draft/regenerate", response_model=RegenResponse)
def regenerate_draft(email_id: str, ctx: AuthContext = Depends(get_auth_context),
                     _rl: AuthContext = Depends(rate_limit("draft", 30))) -> RegenResponse:
    """Re-run RAG drafting for an email off the request cycle (maps to the spec's
    POST /emails/:id/draft:regenerate)."""
    if not OrgScopedDb(ctx.organization_id).fetch_one("emails", {"id": email_id}):
        raise HTTPException(status_code=404, detail="Email not found")
    from ...worker.tasks import draft_email

    job_id = jobs.create_job("draft", organization_id=ctx.organization_id, payload={"email_id": email_id})
    draft_email.apply_async(kwargs={"job_id": job_id, "email_id": email_id,
                                    "organization_id": ctx.organization_id})
    return RegenResponse(job_id=job_id, email_id=email_id)


@router.get("/{email_id}/draft/stream")
def stream_draft_endpoint(email_id: str, ctx: AuthContext = Depends(get_auth_context),
                          _rl: AuthContext = Depends(rate_limit("draft", 30))) -> StreamingResponse:
    """Stream a freshly generated draft token-by-token as Server-Sent Events.

    The text arrives as `data:` events; a final `event: meta` carries the draft
    id and cited sources once persistence completes."""
    if not OrgScopedDb(ctx.organization_id).fetch_one("emails", {"id": email_id}):
        raise HTTPException(status_code=404, detail="Email not found")
    from ...drafting.service import stream_draft

    def event_stream():
        try:
            for piece in stream_draft(ctx.organization_id, email_id):
                if piece.startswith("\n[[DRAFT_META]]"):
                    meta = piece.replace("\n[[DRAFT_META]]", "", 1)
                    yield f"event: meta\ndata: {meta}\n\n"
                else:
                    # Escape newlines so multi-line tokens stay one SSE event.
                    yield "data: " + piece.replace("\n", "\\n") + "\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:  # surface errors to the client stream
            yield f"event: error\ndata: {exc}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Routing (Module 6) ─────────────────────────────────────────────────────
class AssignIn(BaseModel):
    assignee_id: str | None  # null clears the assignment


@router.post("/{email_id}/assign")
def assign_email(email_id: str, body: AssignIn, ctx: AuthContext = Depends(get_auth_context)) -> dict:
    """Manually (re)assign an email to a teammate (the design's 'Reassign')."""
    db = OrgScopedDb(ctx.organization_id)
    if not db.fetch_one("emails", {"id": email_id}):
        raise HTTPException(status_code=404, detail="Email not found")
    if body.assignee_id:
        with connection() as conn:
            member = conn.execute(
                "SELECT 1 FROM memberships WHERE organization_id=%s AND user_id=%s AND deleted_at IS NULL",
                (ctx.organization_id, body.assignee_id),
            ).fetchone()
        if not member:
            raise HTTPException(status_code=400, detail="assignee_id is not a member of this organisation.")

    import json as _json

    with connection() as conn:
        conn.execute("UPDATE emails SET assignee_id=%s WHERE id=%s AND organization_id=%s",
                     (body.assignee_id, email_id, ctx.organization_id))
        conn.execute(
            "INSERT INTO audit_logs (organization_id, actor_id, action, entity) VALUES (%s,%s,'reassigned',%s)",
            (ctx.organization_id, ctx.user_id,
             _json.dumps({"type": "email", "id": email_id, "assignee_id": body.assignee_id})),
        )
    return {"status": "assigned", "email_id": email_id, "assignee_id": body.assignee_id}


@router.post("/{email_id}/route")
def route_now(email_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict:
    """Re-run the routing rules for an email immediately (sync)."""
    if not OrgScopedDb(ctx.organization_id).fetch_one("emails", {"id": email_id}):
        raise HTTPException(status_code=404, detail="Email not found")
    from ...routing.service import route_email

    outcome = route_email(ctx.organization_id, email_id)
    return {"email_id": email_id, "rule_id": outcome.rule_id, "assignee_id": outcome.assignee_id,
            "crm_logged": outcome.crm_logged, "slack_notified": outcome.slack_notified}


# ── Send (one-click review-and-send) ────────────────────────────────────────
class SendIn(BaseModel):
    body: str | None = None       # final edited body; falls back to stored draft
    log_to_crm: bool = False


@router.post("/{email_id}/send")
def send_email(email_id: str, body: SendIn, ctx: AuthContext = Depends(get_auth_context)) -> dict:
    """Mark the reviewed draft as sent and the email as handled, with audit.

    NOTE: actual outbound delivery via the mail provider is a follow-up; this
    records the human's send action (the core human-in-the-loop step) and, if
    requested, a CRM log entry."""
    with connection() as conn:
        email = conn.execute(
            "SELECT id FROM emails WHERE id=%s AND organization_id=%s AND deleted_at IS NULL",
            (email_id, ctx.organization_id),
        ).fetchone()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        draft = conn.execute(
            "SELECT id, body FROM drafts WHERE email_id=%s AND organization_id=%s AND deleted_at IS NULL "
            "AND status IN ('draft','edited') ORDER BY created_at DESC LIMIT 1",
            (email_id, ctx.organization_id),
        ).fetchone()
        if not draft:
            raise HTTPException(status_code=400, detail="No draft to send for this email.")

        final_body = body.body if body.body is not None else draft["body"]
        was_edited = body.body is not None and body.body.strip() != (draft["body"] or "").strip()
        with conn.transaction():
            conn.execute(
                "UPDATE drafts SET body=%s, status='sent', was_edited=%s, sent_by=%s, sent_at=now() WHERE id=%s",
                (final_body, was_edited, ctx.user_id, draft["id"]),
            )
            conn.execute("UPDATE emails SET status='sent' WHERE id=%s AND organization_id=%s",
                         (email_id, ctx.organization_id))
            conn.execute(
                "INSERT INTO audit_logs (organization_id, actor_id, action, entity) VALUES (%s,%s,'sent',%s)",
                (ctx.organization_id, ctx.user_id,
                 _json.dumps({"type": "email", "id": email_id, "draft_id": str(draft["id"]),
                              "log_to_crm": body.log_to_crm})),
            )
    return {"status": "sent", "email_id": email_id, "logged_to_crm": body.log_to_crm}
