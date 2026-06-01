"""Persistence for connected mailboxes (email_accounts), with tokens/credentials
encrypted at rest."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from ..db import connection
from ..security.crypto import get_cipher


def upsert_account(
    organization_id: str,
    provider: str,
    email_address: str,
    secrets: dict[str, Any],
    *,
    status: str = "connected",
) -> dict:
    """Create or reconnect a mailbox. `secrets` is the OAuth token bundle (gmail/
    outlook) or IMAP credentials; it is encrypted before storage."""
    blob = get_cipher().encrypt_json(secrets)
    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO email_accounts (organization_id, provider, email_address, oauth_tokens, status)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (organization_id, lower(email_address)) WHERE deleted_at IS NULL
            DO UPDATE SET oauth_tokens = EXCLUDED.oauth_tokens,
                          provider = EXCLUDED.provider,
                          status = EXCLUDED.status
            RETURNING id, organization_id, provider, email_address, status, last_synced_at
            """,
            (organization_id, provider, email_address, blob, status),
        ).fetchone()
    return row


def list_accounts(organization_id: str) -> list[dict]:
    with connection() as conn:
        return conn.execute(
            """
            SELECT id, provider, email_address, status, last_synced_at, created_at
            FROM email_accounts
            WHERE organization_id = %s AND deleted_at IS NULL
            ORDER BY created_at DESC
            """,
            (organization_id,),
        ).fetchall()


def get_account(organization_id: str, account_id: str) -> dict | None:
    with connection() as conn:
        return conn.execute(
            "SELECT * FROM email_accounts WHERE id = %s AND organization_id = %s AND deleted_at IS NULL",
            (account_id, organization_id),
        ).fetchone()


def load_secrets(account_row: dict) -> dict:
    if not account_row.get("oauth_tokens"):
        return {}
    return get_cipher().decrypt_json(account_row["oauth_tokens"])


def save_secrets(organization_id: str, account_id: str, secrets: dict) -> None:
    blob = get_cipher().encrypt_json(secrets)
    with connection() as conn:
        conn.execute(
            "UPDATE email_accounts SET oauth_tokens = %s WHERE id = %s AND organization_id = %s",
            (blob, account_id, organization_id),
        )


def set_status(organization_id: str, account_id: str, status: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE email_accounts SET status = %s WHERE id = %s AND organization_id = %s",
            (status, account_id, organization_id),
        )


def update_watermark(organization_id: str, account_id: str, ts: datetime) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE email_accounts SET last_synced_at = %s WHERE id = %s AND organization_id = %s",
            (ts, account_id, organization_id),
        )
