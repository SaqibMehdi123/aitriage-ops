"""Poll one connected mailbox and ingest any new messages.

Handles OAuth token refresh (and re-persisting refreshed tokens), fetching since
the account watermark, idempotent ingestion of each message, and advancing the
watermark. Called from the worker's scheduled/triggered sync task.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..logging import get_logger
from . import accounts
from .providers import get_connector
from .providers.base import TokenBundle
from .service import ingest_email

log = get_logger(__name__)


def sync_account(organization_id: str, account_id: str) -> dict:
    account = accounts.get_account(organization_id, account_id)
    if not account:
        raise ValueError(f"Account {account_id} not found for org {organization_id}")

    provider = account["provider"]
    connector = get_connector(provider)
    secrets = accounts.load_secrets(account)
    since = account.get("last_synced_at")

    # Skip accounts with no usable credentials (e.g. the demo "manual" mailbox
    # used by /emails/ingest) rather than marking them errored.
    if provider == "imap" and not secrets.get("host"):
        log.info("sync_skipped_no_credentials", account_id=account_id, provider=provider)
        return {"fetched": 0, "created": 0, "duplicates": 0, "skipped": True}
    if provider in ("gmail", "outlook") and not secrets.get("access_token"):
        log.info("sync_skipped_no_credentials", account_id=account_id, provider=provider)
        return {"fetched": 0, "created": 0, "duplicates": 0, "skipped": True}

    try:
        if provider == "imap":
            messages = connector.fetch_new(secrets, since)
        else:
            bundle = TokenBundle.from_dict(secrets)
            if bundle.is_expired:
                bundle = connector.refresh(bundle)
                accounts.save_secrets(organization_id, account_id, bundle.to_dict())
            messages = connector.fetch_new(bundle, since)
    except Exception as exc:
        accounts.set_status(organization_id, account_id, "error")
        log.error("sync_failed", account_id=account_id, provider=provider, error=str(exc))
        raise

    created = 0
    duplicates = 0
    for inbound in messages:
        result = ingest_email(organization_id, account_id, inbound)
        if result.created:
            created += 1
        else:
            duplicates += 1

    accounts.update_watermark(organization_id, account_id, datetime.now(timezone.utc))
    accounts.set_status(organization_id, account_id, "connected")
    log.info("sync_complete", account_id=account_id, fetched=len(messages),
             created=created, duplicates=duplicates)
    return {"fetched": len(messages), "created": created, "duplicates": duplicates}
