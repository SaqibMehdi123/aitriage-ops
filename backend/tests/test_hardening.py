"""Org settings + per-tenant rate limiter (DB/Redis integration)."""
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


@pytest.mark.skipif(not DB_OK, reason="database not reachable")
def test_org_settings_roundtrip():
    from triage.orgsettings import get_org_settings, upsert_org_settings

    with connection() as conn:
        org = str(conn.execute("INSERT INTO organizations (name) VALUES ('Set Test') RETURNING id").fetchone()["id"])
    try:
        assert get_org_settings(org) == {"pii_redaction": False, "retention_days": None}
        upsert_org_settings(org, pii_redaction=True, retention_days=30)
        got = get_org_settings(org)
        assert got["pii_redaction"] is True and got["retention_days"] == 30
        # update again (conflict path)
        upsert_org_settings(org, pii_redaction=False, retention_days=None)
        assert get_org_settings(org) == {"pii_redaction": False, "retention_days": None}
    finally:
        with connection() as conn:
            conn.execute("DELETE FROM org_settings WHERE organization_id = %s", (org,))
            conn.execute("DELETE FROM organizations WHERE id = %s", (org,))


def test_rate_limiter_blocks_after_limit():
    from fastapi import HTTPException

    from triage.api.ratelimit import rate_limit, _redis
    from triage.auth import AuthContext

    try:
        _redis().ping()
    except Exception:
        pytest.skip("redis not reachable")

    dep = rate_limit("unittest", limit=3, window_seconds=60)
    ctx = AuthContext(user_id="u", email="e@x.com", organization_id=str(uuid.uuid4()), role="owner")

    # First 3 allowed
    for _ in range(3):
        assert dep(ctx) is ctx
    # 4th exceeds the limit
    with pytest.raises(HTTPException) as exc:
        dep(ctx)
    assert exc.value.status_code == 429
