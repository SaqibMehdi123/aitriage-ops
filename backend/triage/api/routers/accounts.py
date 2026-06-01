"""Mailbox connection endpoints — OAuth start/callback, IMAP connect, sync, list.

OAuth state: because the provider redirects the *browser* (which carries no API
bearer token) back to our callback, we carry the tenant identity in an
encrypted, short-lived `state` token rather than trusting anything from the
provider. The callback decrypts it to recover the organization.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context, require_admin
from ...config import get_settings
from ...ingestion import accounts
from ...ingestion.providers import GmailConnector, GraphConnector, ImapConnector
from ...ingestion.providers.base import TokenBundle
from ...security.crypto import get_cipher
from ... import jobs

router = APIRouter(prefix="/accounts", tags=["accounts"])

_STATE_TTL = 600  # seconds


def _make_state(organization_id: str, provider: str) -> str:
    return get_cipher().encrypt_json(
        {"org": organization_id, "provider": provider, "ts": time.time()}
    ).decode()


def _read_state(state: str) -> tuple[str, str]:
    try:
        data = get_cipher().decrypt_json(state.encode())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")
    if time.time() - data.get("ts", 0) > _STATE_TTL:
        raise HTTPException(status_code=400, detail="OAuth state expired — retry the connection.")
    return data["org"], data["provider"]


def _enqueue_initial_sync(organization_id: str, account_id: str) -> None:
    from ...worker.tasks import sync_account

    job_id = jobs.create_job("ingest", organization_id=organization_id, payload={"account_id": account_id})
    sync_account.apply_async(kwargs={"organization_id": organization_id,
                                     "account_id": account_id, "job_id": job_id})


# -- listing -------------------------------------------------------------
class AccountOut(BaseModel):
    id: str
    provider: str
    email_address: str
    status: str
    last_synced_at: str | None = None


@router.get("", response_model=list[AccountOut])
def list_connected(ctx: AuthContext = Depends(get_auth_context)) -> list[AccountOut]:
    rows = accounts.list_accounts(ctx.organization_id)
    return [
        AccountOut(
            id=str(r["id"]), provider=r["provider"], email_address=r["email_address"],
            status=r["status"], last_synced_at=r["last_synced_at"].isoformat() if r["last_synced_at"] else None,
        )
        for r in rows
    ]


# -- OAuth start ---------------------------------------------------------
class ConnectUrlOut(BaseModel):
    auth_url: str


@router.post("/connect/google", response_model=ConnectUrlOut)
def connect_google(ctx: AuthContext = Depends(require_admin)) -> ConnectUrlOut:
    state = _make_state(ctx.organization_id, "gmail")
    return ConnectUrlOut(auth_url=GmailConnector().build_auth_url(state))


@router.post("/connect/microsoft", response_model=ConnectUrlOut)
def connect_microsoft(ctx: AuthContext = Depends(require_admin)) -> ConnectUrlOut:
    state = _make_state(ctx.organization_id, "outlook")
    return ConnectUrlOut(auth_url=GraphConnector().build_auth_url(state))


# -- OAuth callbacks -----------------------------------------------------
@router.get("/connect/google/callback")
def google_callback(code: str = Query(...), state: str = Query(...)) -> RedirectResponse:
    org_id, _ = _read_state(state)
    connector = GmailConnector()
    bundle = connector.exchange_code(code)
    address = connector.get_email_address(bundle)
    account = accounts.upsert_account(org_id, "gmail", address, bundle.to_dict())
    _enqueue_initial_sync(org_id, str(account["id"]))
    return RedirectResponse(url=f"{get_settings().frontend_origin}/settings?connected=gmail")


@router.get("/connect/microsoft/callback")
def microsoft_callback(code: str = Query(...), state: str = Query(...)) -> RedirectResponse:
    org_id, _ = _read_state(state)
    connector = GraphConnector()
    bundle = connector.exchange_code(code)
    address = connector.get_email_address(bundle)
    account = accounts.upsert_account(org_id, "outlook", address, bundle.to_dict())
    _enqueue_initial_sync(org_id, str(account["id"]))
    return RedirectResponse(url=f"{get_settings().frontend_origin}/settings?connected=outlook")


# -- IMAP connect --------------------------------------------------------
class ImapConnectIn(BaseModel):
    host: str
    port: int = 993
    username: str
    password: str


@router.post("/connect/imap", response_model=AccountOut)
def connect_imap(body: ImapConnectIn, ctx: AuthContext = Depends(require_admin)) -> AccountOut:
    creds = body.model_dump()
    try:
        address = ImapConnector().verify(creds)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"IMAP connection failed: {exc}")
    account = accounts.upsert_account(ctx.organization_id, "imap", address or body.username, creds)
    _enqueue_initial_sync(ctx.organization_id, str(account["id"]))
    return AccountOut(id=str(account["id"]), provider="imap", email_address=account["email_address"],
                      status=account["status"], last_synced_at=None)


# -- manual sync / disconnect -------------------------------------------
@router.post("/{account_id}/sync")
def trigger_sync(account_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict:
    if not accounts.get_account(ctx.organization_id, account_id):
        raise HTTPException(status_code=404, detail="Account not found")
    _enqueue_initial_sync(ctx.organization_id, account_id)
    return {"status": "sync_enqueued", "account_id": account_id}


@router.delete("/{account_id}")
def disconnect(account_id: str, ctx: AuthContext = Depends(require_admin)) -> dict:
    from ...db import OrgScopedDb

    ok = OrgScopedDb(ctx.organization_id).soft_delete("email_accounts", account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "disconnected", "account_id": account_id}
