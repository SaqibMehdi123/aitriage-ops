"""Routing tests: pure rule evaluation + DB route_email with mocked notify."""
from __future__ import annotations

import uuid

import pytest

from triage.routing.engine import build_context, evaluate_conditions, first_matching_rule


# ── Pure engine tests (no DB) ──────────────────────────────────────────────
def test_all_conditions_must_match():
    ctx = {"category": "Support", "urgency": "high", "text": "login broken"}
    cond = {"all": [{"field": "category", "op": "eq", "value": "Support"},
                    {"field": "urgency", "op": "eq", "value": "high"}]}
    assert evaluate_conditions(cond, ctx) is True
    ctx2 = {**ctx, "urgency": "low"}
    assert evaluate_conditions(cond, ctx2) is False


def test_keyword_matches_against_text():
    ctx = {"text": "Please check invoice #4092 for billing errors", "category": "Billing"}
    assert evaluate_conditions({"all": [{"field": "keyword", "value": "billing"}]}, ctx) is True
    assert evaluate_conditions({"all": [{"field": "keyword", "value": "refund"}]}, ctx) is False


def test_any_group_or_semantics():
    ctx = {"category": "Sales", "text": ""}
    cond = {"any": [{"field": "category", "value": "Support"},
                    {"field": "category", "value": "Sales"}]}
    assert evaluate_conditions(cond, ctx) is True


def test_in_operator():
    ctx = {"urgency": "high", "text": ""}
    assert evaluate_conditions({"all": [{"field": "urgency", "op": "in", "value": ["high", "normal"]}]}, ctx)


def test_empty_conditions_never_match():
    assert evaluate_conditions({}, {"category": "Support", "text": ""}) is False
    assert evaluate_conditions({"all": []}, {"category": "Support", "text": ""}) is False


def test_flat_list_treated_as_all():
    ctx = {"category": "Spam", "text": ""}
    assert evaluate_conditions([{"field": "category", "value": "Spam"}], ctx) is True


def test_first_matching_rule_respects_order():
    ctx = {"category": "Support", "urgency": "high", "text": ""}
    rules = [
        {"id": "r1", "conditions": {"all": [{"field": "category", "value": "Billing"}]}},
        {"id": "r2", "conditions": {"all": [{"field": "category", "value": "Support"}]}},
        {"id": "r3", "conditions": {"all": [{"field": "urgency", "value": "high"}]}},
    ]
    assert first_matching_rule(rules, ctx)["id"] == "r2"


def test_build_context_combines_subject_and_body():
    ctx = build_context({"subject": "Help", "body_clean": "cannot login", "from_address": "a@b.com"},
                        {"category": "Support", "urgency": "high"})
    assert ctx["category"] == "Support" and "cannot login" in ctx["text"]


# ── DB integration: route_email applies assignee + audits ──────────────────
try:
    from triage.db import connection

    with connection() as _c:
        _c.execute("SELECT 1")
    DB_OK = True
except Exception:  # pragma: no cover
    DB_OK = False


@pytest.mark.skipif(not DB_OK, reason="database not reachable")
def test_route_email_assigns_by_rule(monkeypatch):
    from triage.routing import service as rsvc

    # Don't hit Slack/CRM during the test.
    monkeypatch.setattr(rsvc, "send_slack", lambda *a, **k: False)
    monkeypatch.setattr(rsvc, "send_crm_webhook", lambda *a, **k: True)

    with connection() as conn:
        org = str(conn.execute("INSERT INTO organizations (name) VALUES ('Route Test') RETURNING id").fetchone()["id"])
        user = str(conn.execute("INSERT INTO users (id, email) VALUES (%s,%s) RETURNING id",
                                (str(uuid.uuid4()), f"u-{uuid.uuid4().hex[:6]}@x.com")).fetchone()["id"])
        conn.execute("INSERT INTO memberships (organization_id, user_id, role) VALUES (%s,%s,'agent')", (org, user))
        acc = conn.execute("INSERT INTO email_accounts (organization_id,provider,email_address,status) "
                           "VALUES (%s,'imap',%s,'connected') RETURNING id", (org, f"a{uuid.uuid4().hex[:5]}@x.local")).fetchone()["id"]
        email = str(conn.execute(
            "INSERT INTO emails (organization_id,account_id,message_id,from_address,subject,body_clean,status) "
            "VALUES (%s,%s,%s,'c@x.com','Login broken','urgent cannot log in','classified') RETURNING id",
            (org, acc, "mid-" + uuid.uuid4().hex)).fetchone()["id"])
        conn.execute("INSERT INTO classifications (organization_id,email_id,category,confidence,urgency) "
                     "VALUES (%s,%s,'Support',0.95,'high')", (org, email))
        import json
        conn.execute(
            "INSERT INTO routing_rules (organization_id, name, priority, conditions, assignee_id, crm_action, is_active) "
            "VALUES (%s,'Urgent support',10,%s::jsonb,%s,%s::jsonb,true)",
            (org, json.dumps({"all": [{"field": "category", "value": "Support"},
                                      {"field": "urgency", "value": "high"}]}),
             user, json.dumps({"webhook_url": "https://example.test/crm"})),
        )

    try:
        outcome = rsvc.route_email(org, email)
        assert outcome.assignee_id == user
        assert outcome.crm_logged is True
        with connection() as conn:
            got = conn.execute("SELECT assignee_id FROM emails WHERE id=%s", (email,)).fetchone()["assignee_id"]
            audited = conn.execute("SELECT count(*) AS n FROM audit_logs WHERE organization_id=%s AND action='routed'", (org,)).fetchone()["n"]
        assert str(got) == user
        assert audited == 1
    finally:
        with connection() as conn:
            for t in ("audit_logs", "jobs", "classifications", "drafts", "routing_rules", "emails", "email_accounts", "memberships"):
                conn.execute(f"DELETE FROM {t} WHERE organization_id = %s", (org,))
            conn.execute("DELETE FROM organizations WHERE id = %s", (org,))
            conn.execute("DELETE FROM users WHERE id = %s", (user,))
