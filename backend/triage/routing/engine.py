"""Pure rule-evaluation logic (no I/O) so it is trivially unit-testable.

A rule's `conditions` is a JSON object:
    {"all": [ {field, op, value}, ... ], "any": [ ... ]}
Both groups are optional; `all` must all match and `any` must have ≥1 match. A
flat list is treated as an `all` group. Empty conditions never match (no
accidental catch-alls).

Supported fields: category, urgency, from_address, subject, keyword (matches
against the combined subject + body text). Operators: eq, ne, contains, in.
"""
from __future__ import annotations

from typing import Any

_KEYWORD_FIELD = "keyword"


def _match_one(cond: dict, ctx: dict) -> bool:
    field = cond.get("field")
    op = (cond.get("op") or "eq").lower()
    value = cond.get("value")

    if field == _KEYWORD_FIELD:
        actual = ctx.get("text", "")
        if not op or op == "eq":
            op = "contains"
    else:
        actual = ctx.get(field)

    if actual is None:
        return False
    a = str(actual).lower()

    if op == "eq":
        return a == str(value).lower()
    if op == "ne":
        return a != str(value).lower()
    if op == "contains":
        return str(value).lower() in a
    if op == "in":
        return a in [str(v).lower() for v in (value or [])]
    return False


def evaluate_conditions(conditions: Any, ctx: dict) -> bool:
    if isinstance(conditions, list):
        conditions = {"all": conditions}
    if not isinstance(conditions, dict):
        return False

    all_group = conditions.get("all") or []
    any_group = conditions.get("any") or []
    if not all_group and not any_group:
        return False

    all_ok = all(_match_one(c, ctx) for c in all_group) if all_group else True
    any_ok = any(_match_one(c, ctx) for c in any_group) if any_group else True
    return all_ok and any_ok


def first_matching_rule(rules: list[dict], ctx: dict) -> dict | None:
    """Return the first rule (already ordered by priority) whose conditions match."""
    for rule in rules:
        if evaluate_conditions(rule.get("conditions"), ctx):
            return rule
    return None


def build_context(email: dict, classification: dict | None) -> dict:
    subject = email.get("subject") or ""
    body = email.get("body_clean") or ""
    return {
        "category": (classification or {}).get("category"),
        "urgency": (classification or {}).get("urgency"),
        "from_address": email.get("from_address") or "",
        "subject": subject,
        "text": f"{subject}\n{body}",
    }
