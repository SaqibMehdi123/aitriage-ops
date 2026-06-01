"""Classification threshold-routing tests with a mocked LLM (no API key needed).

Verifies the routing rules around the confidence threshold and the failure
fallback, plus that the classification row is persisted, against the real DB.
"""
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
    from triage.classification import service as clf
    from triage.classification.schemas import ClassificationResult
    from triage.llm import LLMError


@pytest.fixture
def org_with_email():
    with connection() as conn:
        org = conn.execute(
            "INSERT INTO organizations (name) VALUES ('Clf Test') RETURNING id"
        ).fetchone()
        org_id = str(org["id"])
        acc = conn.execute(
            "INSERT INTO email_accounts (organization_id, provider, email_address, status) "
            "VALUES (%s, 'imap', %s, 'connected') RETURNING id",
            (org_id, f"acc-{uuid.uuid4().hex[:6]}@x.local"),
        ).fetchone()
        email = conn.execute(
            "INSERT INTO emails (organization_id, account_id, message_id, from_address, subject, body_clean, status) "
            "VALUES (%s, %s, %s, 'c@x.com', 'Help', 'I cannot log in', 'new') RETURNING id",
            (org_id, acc["id"], f"mid-{uuid.uuid4().hex[:8]}"),
        ).fetchone()
    yield org_id, str(email["id"])
    with connection() as conn:
        for t in ("audit_logs", "jobs", "classifications", "drafts", "emails", "email_accounts"):
            conn.execute(f"DELETE FROM {t} WHERE organization_id = %s", (org_id,))
        conn.execute("DELETE FROM organizations WHERE id = %s", (org_id,))


def _patch(monkeypatch, result):
    monkeypatch.setattr(clf, "classify_text", lambda *a, **k: result)


def test_high_confidence_support_is_classified_and_draftable(org_with_email, monkeypatch):
    org_id, email_id = org_with_email
    _patch(monkeypatch, ClassificationResult(category="Support", confidence=0.95, urgency="high"))

    out = clf.classify_email(org_id, email_id)

    assert out.status == "classified"
    assert out.draftable is True
    with connection() as conn:
        row = conn.execute("SELECT category, confidence, urgency FROM classifications WHERE email_id=%s", (email_id,)).fetchone()
        status = conn.execute("SELECT status FROM emails WHERE id=%s", (email_id,)).fetchone()["status"]
    assert row["category"] == "Support" and float(row["confidence"]) == pytest.approx(0.95)
    assert status == "classified"


def test_low_confidence_routes_to_review(org_with_email, monkeypatch):
    org_id, email_id = org_with_email
    _patch(monkeypatch, ClassificationResult(category="Sales", confidence=0.40, urgency="normal"))

    out = clf.classify_email(org_id, email_id)

    assert out.status == "review"
    assert out.draftable is False


def test_spam_is_classified_but_not_draftable(org_with_email, monkeypatch):
    org_id, email_id = org_with_email
    _patch(monkeypatch, ClassificationResult(category="Spam", confidence=0.99, urgency="low"))

    out = clf.classify_email(org_id, email_id)

    assert out.status == "classified"
    assert out.draftable is False


def test_llm_failure_falls_back_to_review(org_with_email, monkeypatch):
    org_id, email_id = org_with_email

    def _raise(*a, **k):
        raise LLMError("model unavailable")

    monkeypatch.setattr(clf, "classify_text", _raise)

    out = clf.classify_email(org_id, email_id)

    assert out.category == "Other"
    assert out.confidence == 0.0
    assert out.status == "review"


def test_reclassify_updates_existing_row(org_with_email, monkeypatch):
    org_id, email_id = org_with_email
    _patch(monkeypatch, ClassificationResult(category="Support", confidence=0.9, urgency="normal"))
    clf.classify_email(org_id, email_id)
    _patch(monkeypatch, ClassificationResult(category="Billing", confidence=0.85, urgency="low"))
    clf.classify_email(org_id, email_id)

    with connection() as conn:
        rows = conn.execute("SELECT category FROM classifications WHERE email_id=%s AND deleted_at IS NULL", (email_id,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["category"] == "Billing"
