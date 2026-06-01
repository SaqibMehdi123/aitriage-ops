"""Apply routing rules to a classified email: assignee + CRM action + Slack."""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..db import connection
from ..logging import get_logger
from .engine import build_context, first_matching_rule
from .notify import send_crm_webhook, send_slack

log = get_logger(__name__)


@dataclass
class RouteOutcome:
    email_id: str
    rule_id: str | None
    assignee_id: str | None
    crm_logged: bool
    slack_notified: bool


def route_email(organization_id: str, email_id: str) -> RouteOutcome:
    with connection() as conn:
        email = conn.execute(
            "SELECT id, from_address, subject, body_clean FROM emails "
            "WHERE id = %s AND organization_id = %s AND deleted_at IS NULL",
            (email_id, organization_id),
        ).fetchone()
        if not email:
            raise ValueError(f"Email {email_id} not found for org {organization_id}")
        classification = conn.execute(
            "SELECT category, urgency FROM classifications WHERE email_id = %s AND deleted_at IS NULL",
            (email_id,),
        ).fetchone()
        rules = conn.execute(
            "SELECT id, conditions, assignee_id, crm_action FROM routing_rules "
            "WHERE organization_id = %s AND is_active = true AND deleted_at IS NULL "
            "ORDER BY priority ASC, created_at ASC",
            (organization_id,),
        ).fetchall()

    ctx = build_context(email, classification)
    rule = first_matching_rule(rules, ctx)

    assignee_id = None
    crm_logged = False
    slack_notified = False

    if rule:
        assignee_id = str(rule["assignee_id"]) if rule.get("assignee_id") else None
        if assignee_id:
            _assign(organization_id, email_id, assignee_id)
        crm_logged = _apply_crm(rule.get("crm_action"), email, ctx)
        slack_notified = _notify(ctx, assignee_id, matched=True)
        _audit(organization_id, "routed", {
            "type": "email", "id": email_id, "rule_id": str(rule["id"]),
            "assignee_id": assignee_id, "crm_logged": crm_logged,
        })
        log.info("email_routed", email_id=email_id, rule_id=str(rule["id"]), assignee_id=assignee_id)
    else:
        # No rule matched — the email stays unassigned for manual pickup, but is
        # still explicitly owned by being surfaced in the unassigned queue.
        _audit(organization_id, "routed", {"type": "email", "id": email_id, "rule_id": None})
        log.info("email_routed_no_match", email_id=email_id)

    return RouteOutcome(email_id=email_id, rule_id=str(rule["id"]) if rule else None,
                        assignee_id=assignee_id, crm_logged=crm_logged, slack_notified=slack_notified)


def _assign(organization_id: str, email_id: str, assignee_id: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE emails SET assignee_id = %s WHERE id = %s AND organization_id = %s",
            (assignee_id, email_id, organization_id),
        )


def _apply_crm(crm_action: dict | None, email: dict, ctx: dict) -> bool:
    if not crm_action:
        return False
    webhook_url = crm_action.get("webhook_url")
    if webhook_url:
        payload = {
            "email_id": str(email["id"]),
            "from": email.get("from_address"),
            "subject": email.get("subject"),
            "category": ctx.get("category"),
            "urgency": ctx.get("urgency"),
            "crm_action": crm_action,
        }
        return send_crm_webhook(webhook_url, payload)
    # No webhook configured: the action is recorded in the audit log only.
    return True


def _notify(ctx: dict, assignee_id: str | None, *, matched: bool) -> bool:
    who = assignee_id or "the unassigned queue"
    text = (
        f":inbox_tray: New *{ctx.get('category') or 'Unclassified'}* email "
        f"({ctx.get('urgency') or 'normal'}) from {ctx.get('from_address')}\n"
        f"> {ctx.get('subject') or '(no subject)'}\n"
        f"Routed to: {who}"
    )
    return send_slack(text)


def _audit(organization_id: str, action: str, entity: dict) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (organization_id, actor_id, action, entity) VALUES (%s, NULL, %s, %s)",
            (organization_id, action, json.dumps(entity)),
        )
