"""Reply-draft generation, persistence (with citations), and streaming."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterator

from ..config import get_settings
from ..db import connection
from ..knowledge.retrieval import RetrievedChunk, retrieve
from ..llm import get_llm
from ..logging import get_logger
from .prompts import PROMPT_VERSION, build_messages

log = get_logger(__name__)


def model_version() -> str:
    s = get_settings()
    return f"{s.llm_provider}:{s.llm_model_smart}/{PROMPT_VERSION}"


@dataclass
class DraftContext:
    thread_text: str
    category: str | None
    chunks: list[RetrievedChunk]


@dataclass
class DraftResult:
    draft_id: str
    body: str
    sources: list[dict]


def _gather_context(organization_id: str, email_id: str) -> tuple[dict, DraftContext]:
    with connection() as conn:
        email = conn.execute(
            "SELECT id, thread_id, from_address, subject, body_clean FROM emails "
            "WHERE id = %s AND organization_id = %s AND deleted_at IS NULL",
            (email_id, organization_id),
        ).fetchone()
        if not email:
            raise ValueError(f"Email {email_id} not found for org {organization_id}")

        # Assemble the thread transcript (oldest first) for context.
        if email["thread_id"]:
            thread = conn.execute(
                "SELECT from_address, subject, body_clean, received_at FROM emails "
                "WHERE organization_id = %s AND thread_id = %s AND deleted_at IS NULL "
                "ORDER BY received_at ASC NULLS FIRST",
                (organization_id, email["thread_id"]),
            ).fetchall()
        else:
            thread = [email]

        category = conn.execute(
            "SELECT category FROM classifications WHERE email_id = %s AND deleted_at IS NULL",
            (email_id,),
        ).fetchone()

    transcript = "\n\n---\n\n".join(
        f"From: {m['from_address']}\nSubject: {m.get('subject') or '(no subject)'}\n\n{(m.get('body_clean') or '').strip()}"
        for m in thread
    )

    # Retrieve KB grounding from the email's own text.
    query = f"{email.get('subject') or ''}\n{(email.get('body_clean') or '')[:1000]}"
    chunks = retrieve(organization_id, query)

    return email, DraftContext(
        thread_text=transcript,
        category=category["category"] if category else None,
        chunks=chunks,
    )


def _sources_payload(chunks: list[RetrievedChunk]) -> list[dict]:
    return [
        {"chunk_id": c.chunk_id, "doc_id": c.doc_id, "title": c.title,
         "source": c.source, "score": round(c.score, 4)}
        for c in chunks
    ]


def draft_for_email(organization_id: str, email_id: str) -> DraftResult:
    """Generate a complete draft (non-streaming) and persist it with citations."""
    _email, ctx = _gather_context(organization_id, email_id)
    messages = build_messages(ctx.thread_text, ctx.category, ctx.chunks)

    resp = get_llm().complete(messages, tier="smart", temperature=0.3,
                              max_tokens=700, trace_name="draft_email")
    sources = _sources_payload(ctx.chunks)
    draft_id = _persist_draft(organization_id, email_id, resp.text.strip(), sources)
    _set_email_status(organization_id, email_id, "drafted")
    _audit(organization_id, "drafted", {"type": "email", "id": email_id,
                                        "draft_id": draft_id, "sources": len(sources)})
    log.info("draft_created", email_id=email_id, draft_id=draft_id, sources=len(sources))
    return DraftResult(draft_id=draft_id, body=resp.text.strip(), sources=sources)


def stream_draft(organization_id: str, email_id: str) -> Iterator[str]:
    """Yield draft tokens as they arrive, then persist the full draft + citations.

    The final yielded item is a sentinel JSON line beginning with the marker
    '\\n[[DRAFT_META]]' carrying the draft id and sources, so the client can
    record them after the text stream completes."""
    _email, ctx = _gather_context(organization_id, email_id)
    messages = build_messages(ctx.thread_text, ctx.category, ctx.chunks)

    buffer: list[str] = []
    for token in get_llm().stream(messages, tier="smart", temperature=0.3):
        buffer.append(token)
        yield token

    body = "".join(buffer).strip()
    sources = _sources_payload(ctx.chunks)
    draft_id = _persist_draft(organization_id, email_id, body, sources)
    _set_email_status(organization_id, email_id, "drafted")
    _audit(organization_id, "drafted", {"type": "email", "id": email_id, "draft_id": draft_id})
    yield "\n[[DRAFT_META]]" + json.dumps({"draft_id": draft_id, "sources": sources})


def _persist_draft(organization_id: str, email_id: str, body: str, sources: list[dict]) -> str:
    """Replace the current editable draft for the email (keeps sent ones)."""
    with connection() as conn, conn.transaction():
        existing = conn.execute(
            "SELECT id FROM drafts WHERE email_id = %s AND status = 'draft' AND deleted_at IS NULL",
            (email_id,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE drafts SET body = %s, sources = %s, model = %s WHERE id = %s",
                (body, json.dumps(sources), model_version(), existing["id"]),
            )
            return str(existing["id"])
        row = conn.execute(
            "INSERT INTO drafts (organization_id, email_id, body, sources, status, model) "
            "VALUES (%s, %s, %s, %s, 'draft', %s) RETURNING id",
            (organization_id, email_id, body, json.dumps(sources), model_version()),
        ).fetchone()
        return str(row["id"])


def _set_email_status(organization_id: str, email_id: str, status: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE emails SET status = %s WHERE id = %s AND organization_id = %s",
            (status, email_id, organization_id),
        )


def _audit(organization_id: str, action: str, entity: dict) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (organization_id, actor_id, action, entity) VALUES (%s, NULL, %s, %s)",
            (organization_id, action, json.dumps(entity)),
        )
