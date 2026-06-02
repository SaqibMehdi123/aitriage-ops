"""Per-organisation settings (privacy controls) with sane defaults."""
from __future__ import annotations

from functools import lru_cache

from .db import connection

DEFAULTS = {"pii_redaction": False, "retention_days": None}


def get_org_settings(organization_id: str) -> dict:
    with connection() as conn:
        row = conn.execute(
            "SELECT pii_redaction, retention_days FROM org_settings WHERE organization_id = %s",
            (organization_id,),
        ).fetchone()
    if not row:
        return dict(DEFAULTS)
    return {"pii_redaction": row["pii_redaction"], "retention_days": row["retention_days"]}


def upsert_org_settings(organization_id: str, *, pii_redaction: bool, retention_days: int | None) -> dict:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO org_settings (organization_id, pii_redaction, retention_days)
            VALUES (%s, %s, %s)
            ON CONFLICT (organization_id)
            DO UPDATE SET pii_redaction = EXCLUDED.pii_redaction,
                          retention_days = EXCLUDED.retention_days
            """,
            (organization_id, pii_redaction, retention_days),
        )
    return {"pii_redaction": pii_redaction, "retention_days": retention_days}
