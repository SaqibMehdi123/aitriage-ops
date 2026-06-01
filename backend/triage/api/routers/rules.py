"""Routing-rule management (Module 6). Maps to GET/POST/PUT /rules in the spec."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...auth import AuthContext, get_auth_context, require_admin
from ...db import connection

router = APIRouter(prefix="/rules", tags=["rules"])


class RuleIn(BaseModel):
    name: str | None = None
    priority: int = 100
    conditions: dict = Field(default_factory=dict)
    assignee_id: str | None = None
    crm_action: dict | None = None
    is_active: bool = True


class RuleOut(BaseModel):
    id: str
    name: str | None
    priority: int
    conditions: dict
    assignee_id: str | None
    crm_action: dict | None
    is_active: bool


def _validate_assignee(organization_id: str, assignee_id: str | None) -> None:
    if not assignee_id:
        return
    with connection() as conn:
        ok = conn.execute(
            "SELECT 1 FROM memberships WHERE organization_id = %s AND user_id = %s AND deleted_at IS NULL",
            (organization_id, assignee_id),
        ).fetchone()
    if not ok:
        raise HTTPException(status_code=400, detail="assignee_id is not a member of this organisation.")


def _row_to_out(r: dict) -> RuleOut:
    return RuleOut(
        id=str(r["id"]), name=r.get("name"), priority=r["priority"],
        conditions=r.get("conditions") or {}, assignee_id=str(r["assignee_id"]) if r.get("assignee_id") else None,
        crm_action=r.get("crm_action"), is_active=r["is_active"],
    )


@router.get("", response_model=list[RuleOut])
def list_rules(ctx: AuthContext = Depends(get_auth_context)) -> list[RuleOut]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM routing_rules WHERE organization_id = %s AND deleted_at IS NULL "
            "ORDER BY priority ASC, created_at ASC",
            (ctx.organization_id,),
        ).fetchall()
    return [_row_to_out(r) for r in rows]


@router.post("", response_model=RuleOut)
def create_rule(body: RuleIn, ctx: AuthContext = Depends(require_admin)) -> RuleOut:
    _validate_assignee(ctx.organization_id, body.assignee_id)
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO routing_rules (organization_id, name, priority, conditions, assignee_id, crm_action, is_active) "
            "VALUES (%s, %s, %s, %s::jsonb, %s, %s::jsonb, %s) RETURNING *",
            (ctx.organization_id, body.name, body.priority, json.dumps(body.conditions),
             body.assignee_id, json.dumps(body.crm_action) if body.crm_action else None, body.is_active),
        ).fetchone()
    return _row_to_out(row)


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: str, body: RuleIn, ctx: AuthContext = Depends(require_admin)) -> RuleOut:
    _validate_assignee(ctx.organization_id, body.assignee_id)
    with connection() as conn:
        row = conn.execute(
            "UPDATE routing_rules SET name=%s, priority=%s, conditions=%s::jsonb, assignee_id=%s, "
            "crm_action=%s::jsonb, is_active=%s WHERE id=%s AND organization_id=%s AND deleted_at IS NULL RETURNING *",
            (body.name, body.priority, json.dumps(body.conditions), body.assignee_id,
             json.dumps(body.crm_action) if body.crm_action else None, body.is_active,
             rule_id, ctx.organization_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _row_to_out(row)


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, ctx: AuthContext = Depends(require_admin)) -> dict:
    with connection() as conn:
        cur = conn.execute(
            "UPDATE routing_rules SET deleted_at = now() WHERE id=%s AND organization_id=%s AND deleted_at IS NULL",
            (rule_id, ctx.organization_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted", "rule_id": rule_id}
