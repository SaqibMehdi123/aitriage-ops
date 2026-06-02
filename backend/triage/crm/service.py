"""CRM interaction logging — dispatches to the configured provider."""
from __future__ import annotations

from email.utils import parseaddr

import httpx

from ..config import get_settings
from ..logging import get_logger

log = get_logger(__name__)


def log_interaction(*, contact_email: str, subject: str | None, category: str | None,
                    reply_body: str) -> bool:
    """Record the sent reply in the CRM. Returns True if logged, False otherwise."""
    settings = get_settings()
    provider = settings.crm_provider
    email_addr = parseaddr(contact_email or "")[1] or contact_email

    payload = {
        "contact_email": email_addr,
        "subject": subject or "",
        "category": category,
        "reply": reply_body,
    }
    try:
        if provider == "webhook":
            return _webhook(settings.crm_webhook_url, payload)
        if provider == "hubspot":
            return _hubspot(settings.hubspot_token, payload)
        return False  # 'none'
    except Exception as exc:  # never block the send
        log.warning("crm_log_failed", provider=provider, error=str(exc))
        return False


def _webhook(url: str, payload: dict) -> bool:
    if not url:
        return False
    with httpx.Client(timeout=15) as client:
        client.post(url, json=payload)
    log.info("crm_webhook_logged", contact=payload["contact_email"])
    return True


def _hubspot(token: str, payload: dict) -> bool:
    if not token:
        return False
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    email_addr = payload["contact_email"]
    with httpx.Client(timeout=20, headers=headers) as client:
        # 1) Upsert the contact (create; if it already exists, look up its id).
        contact_id = None
        resp = client.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            json={"properties": {"email": email_addr}},
        )
        if resp.status_code in (200, 201):
            contact_id = resp.json()["id"]
        elif resp.status_code == 409:
            search = client.post(
                "https://api.hubapi.com/crm/v3/objects/contacts/search",
                json={"filterGroups": [{"filters": [
                    {"propertyName": "email", "operator": "EQ", "value": email_addr}]}]},
            )
            results = search.json().get("results", [])
            contact_id = results[0]["id"] if results else None
        else:
            resp.raise_for_status()

        # 2) Attach a note describing the interaction, associated to the contact.
        import time

        note = {
            "properties": {
                "hs_timestamp": int(time.time() * 1000),
                "hs_note_body": f"[{payload.get('category') or 'Email'}] Re: {payload['subject']}\n\n{payload['reply']}",
            }
        }
        if contact_id:
            # association type 202 = note -> contact
            note["associations"] = [{
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
            }]
        client.post("https://api.hubapi.com/crm/v3/objects/notes", json=note).raise_for_status()
    log.info("crm_hubspot_logged", contact=email_addr)
    return True
