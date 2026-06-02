"""Per-organisation settings: PII redaction + data retention (Module 9)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context, require_admin
from ...orgsettings import get_org_settings, upsert_org_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class OrgSettings(BaseModel):
    pii_redaction: bool = False
    retention_days: int | None = None


@router.get("", response_model=OrgSettings)
def read_settings(ctx: AuthContext = Depends(get_auth_context)) -> OrgSettings:
    return OrgSettings(**get_org_settings(ctx.organization_id))


@router.put("", response_model=OrgSettings)
def write_settings(body: OrgSettings, ctx: AuthContext = Depends(require_admin)) -> OrgSettings:
    saved = upsert_org_settings(
        ctx.organization_id,
        pii_redaction=body.pii_redaction,
        retention_days=body.retention_days,
    )
    return OrgSettings(**saved)
