"""Inbound mail intake.

Two entry points:
  * POST /webhooks/mail   — for provider push delivery. Authenticated by a shared
    secret header (the browser/user session is absent here). Idempotent.
  * POST /emails/ingest   — authenticated manual/simulated ingestion, handy for
    demos and tests. If no account_id is given, a per-org "manual" mailbox is
    used so you can drive the pipeline without connecting a real inbox.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context
from ...config import get_settings
from ...ingestion import accounts
from ...ingestion.schemas import InboundEmail
from ...ingestion.service import ingest_email

router = APIRouter(tags=["ingestion"])


class IngestResultOut(BaseModel):
    email_id: str | None
    created: bool
    injection_suspected: bool = False


def _get_or_create_manual_account(organization_id: str) -> str:
    address = "manual@inbox.local"
    for acc in accounts.list_accounts(organization_id):
        if acc["email_address"] == address:
            return str(acc["id"])
    row = accounts.upsert_account(organization_id, "imap", address, {}, status="connected")
    return str(row["id"])


# -- provider push webhook ----------------------------------------------
class WebhookPayload(BaseModel):
    organization_id: str
    account_id: str
    messages: list[InboundEmail]


@router.post("/webhooks/mail")
def mail_webhook(
    payload: WebhookPayload,
    x_webhook_secret: str | None = Header(default=None),
) -> dict:
    secret = get_settings().mail_webhook_secret
    if not secret or x_webhook_secret != secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

    created = duplicates = 0
    for msg in payload.messages:
        result = ingest_email(payload.organization_id, payload.account_id, msg)
        created += int(result.created)
        duplicates += int(not result.created)
    return {"received": len(payload.messages), "created": created, "duplicates": duplicates}


# -- authenticated manual ingest (demo/testing) -------------------------
class ManualIngestIn(BaseModel):
    email: InboundEmail
    account_id: str | None = None


@router.post("/emails/ingest", response_model=IngestResultOut)
def manual_ingest(body: ManualIngestIn, ctx: AuthContext = Depends(get_auth_context)) -> IngestResultOut:
    account_id = body.account_id
    if account_id:
        if not accounts.get_account(ctx.organization_id, account_id):
            raise HTTPException(status_code=404, detail="Account not found")
    else:
        account_id = _get_or_create_manual_account(ctx.organization_id)

    result = ingest_email(ctx.organization_id, account_id, body.email)
    return IngestResultOut(
        email_id=result.email_id,
        created=result.created,
        injection_suspected=result.injection_suspected,
    )
