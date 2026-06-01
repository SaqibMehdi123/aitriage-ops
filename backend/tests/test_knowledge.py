"""Integration tests for KB embed + retrieval (requires DB; uses hash embedder)."""
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
    from triage.knowledge.retrieval import retrieve
    from triage.knowledge.service import create_document, embed_document


@pytest.fixture
def org():
    with connection() as conn:
        row = conn.execute("INSERT INTO organizations (name) VALUES ('KB Test') RETURNING id").fetchone()
    org_id = str(row["id"])
    yield org_id
    with connection() as conn:
        conn.execute("DELETE FROM knowledge_chunks WHERE organization_id = %s", (org_id,))
        conn.execute("DELETE FROM knowledge_docs WHERE organization_id = %s", (org_id,))
        conn.execute("DELETE FROM organizations WHERE id = %s", (org_id,))


def test_embed_creates_chunks_and_marks_synced(org):
    content = "Our refund policy allows returns within 30 days of purchase. " * 30
    doc_id = create_document(org, "Refund Policy", content)
    result = embed_document(org, doc_id)

    assert result.chunks >= 1
    with connection() as conn:
        status = conn.execute("SELECT status FROM knowledge_docs WHERE id=%s", (doc_id,)).fetchone()["status"]
        n = conn.execute("SELECT count(*) AS n FROM knowledge_chunks WHERE doc_id=%s", (doc_id,)).fetchone()["n"]
    assert status == "synced"
    assert n == result.chunks


def test_retrieval_returns_most_relevant_doc(org):
    refund_id = create_document(org, "Refunds", "To request a refund, email billing within 30 days for a full refund.")
    sso_id = create_document(org, "SSO Setup", "Enterprise SAML SSO setup takes 1-2 business days after metadata exchange.")
    embed_document(org, refund_id)
    embed_document(org, sso_id)

    # NOTE: the default 'hash' embedder is lexical (bag-of-words), so the query
    # must share words with the target. Synonym matching ("money back" -> refund)
    # requires a semantic provider (fastembed/openai).
    hits = retrieve(org, "how do I request a refund for billing?", k=3)
    assert hits, "expected at least one retrieved chunk"
    top = hits[0]
    assert top.doc_id == refund_id
    assert 0.0 <= top.score <= 1.0


def test_retrieval_is_org_scoped(org):
    doc_id = create_document(org, "Secret", "internal pricing playbook details")
    embed_document(org, doc_id)

    # A different org must not see this org's chunks.
    other = str(uuid.uuid4())
    hits = retrieve(other, "pricing playbook", k=5)
    assert all(h.doc_id != doc_id for h in hits)
