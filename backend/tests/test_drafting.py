"""Drafting tests with mocked LLM + retrieval (DB required, no API key)."""
from __future__ import annotations

import uuid

import pytest

try:
    from triage.db import connection

    with connection() as _c:
        _c.execute("SELECT 1")
    DB_OK = True
except Exception:  # pragma: no cover
    DB_OK = False

pytestmark = pytest.mark.skipif(not DB_OK, reason="database not reachable")

if DB_OK:
    from triage.drafting import service as draft_svc
    from triage.knowledge.retrieval import RetrievedChunk
    from triage.llm import LLMResponse


class _FakeLLM:
    def __init__(self, text="Hi, thanks for reaching out. Best regards, The Team"):
        self.text = text

    def complete(self, *a, **k):
        return LLMResponse(text=self.text, model="fake/clf", prompt_tokens=10, completion_tokens=20)

    def stream(self, *a, **k):
        for tok in ["Hi, ", "thanks ", "for ", "reaching out."]:
            yield tok


@pytest.fixture
def email_ready():
    with connection() as conn:
        org = conn.execute("INSERT INTO organizations (name) VALUES ('Draft Test') RETURNING id").fetchone()
        org_id = str(org["id"])
        acc = conn.execute(
            "INSERT INTO email_accounts (organization_id, provider, email_address, status) "
            "VALUES (%s,'imap',%s,'connected') RETURNING id",
            (org_id, f"a-{uuid.uuid4().hex[:6]}@x.local"),
        ).fetchone()
        email = conn.execute(
            "INSERT INTO emails (organization_id, account_id, message_id, from_address, subject, body_clean, status) "
            "VALUES (%s,%s,%s,'c@x.com','Refund question','How do I get a refund?','classified') RETURNING id",
            (org_id, acc["id"], f"mid-{uuid.uuid4().hex[:8]}"),
        ).fetchone()
        email_id = str(email["id"])
        conn.execute(
            "INSERT INTO classifications (organization_id, email_id, category, confidence, urgency) "
            "VALUES (%s,%s,'Billing',0.9,'normal')",
            (org_id, email_id),
        )
    yield org_id, email_id
    with connection() as conn:
        for t in ("audit_logs", "jobs", "classifications", "drafts", "emails", "email_accounts"):
            conn.execute(f"DELETE FROM {t} WHERE organization_id = %s", (org_id,))
        conn.execute("DELETE FROM organizations WHERE id = %s", (org_id,))


def _patch(monkeypatch, chunks):
    monkeypatch.setattr(draft_svc, "get_llm", lambda: _FakeLLM())
    monkeypatch.setattr(draft_svc, "retrieve", lambda *a, **k: chunks)


def test_draft_persisted_with_citations_and_status(email_ready, monkeypatch):
    org_id, email_id = email_ready
    chunk = RetrievedChunk(chunk_id=str(uuid.uuid4()), doc_id=str(uuid.uuid4()),
                           content="Refunds within 30 days.", score=0.88, title="Refund Policy")
    _patch(monkeypatch, [chunk])

    result = draft_svc.draft_for_email(org_id, email_id)

    assert result.body.startswith("Hi")
    assert len(result.sources) == 1 and result.sources[0]["title"] == "Refund Policy"
    with connection() as conn:
        row = conn.execute("SELECT body, status, sources FROM drafts WHERE id=%s", (result.draft_id,)).fetchone()
        estatus = conn.execute("SELECT status FROM emails WHERE id=%s", (email_id,)).fetchone()["status"]
    assert row["status"] == "draft"
    assert row["sources"][0]["chunk_id"] == chunk.chunk_id
    assert estatus == "drafted"


def test_regenerate_replaces_editable_draft(email_ready, monkeypatch):
    org_id, email_id = email_ready
    _patch(monkeypatch, [])
    first = draft_svc.draft_for_email(org_id, email_id)
    second = draft_svc.draft_for_email(org_id, email_id)
    assert first.draft_id == second.draft_id  # same editable row reused
    with connection() as conn:
        n = conn.execute("SELECT count(*) AS n FROM drafts WHERE email_id=%s AND deleted_at IS NULL", (email_id,)).fetchone()["n"]
    assert n == 1


def test_stream_yields_tokens_then_persists(email_ready, monkeypatch):
    org_id, email_id = email_ready
    _patch(monkeypatch, [])

    pieces = list(draft_svc.stream_draft(org_id, email_id))
    text_pieces = [p for p in pieces if not p.startswith("\n[[DRAFT_META]]")]
    meta_pieces = [p for p in pieces if p.startswith("\n[[DRAFT_META]]")]

    assert "".join(text_pieces).startswith("Hi, thanks")
    assert len(meta_pieces) == 1
    with connection() as conn:
        n = conn.execute("SELECT count(*) AS n FROM drafts WHERE email_id=%s", (email_id,)).fetchone()["n"]
    assert n == 1
