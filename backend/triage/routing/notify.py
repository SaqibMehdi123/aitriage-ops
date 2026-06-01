"""Outbound notifications for routing. All failures are swallowed and logged —
a down Slack/CRM endpoint must never break email routing (graceful degradation).
"""
from __future__ import annotations

import httpx

from ..config import get_settings
from ..logging import get_logger

log = get_logger(__name__)


def send_slack(text: str) -> bool:
    url = get_settings().slack_webhook_url
    if not url:
        return False
    try:
        with httpx.Client(timeout=10) as client:
            client.post(url, json={"text": text})
        return True
    except Exception as exc:  # pragma: no cover - network
        log.warning("slack_notify_failed", error=str(exc))
        return False


def send_crm_webhook(url: str, payload: dict) -> bool:
    if not url:
        return False
    try:
        with httpx.Client(timeout=10) as client:
            client.post(url, json=payload)
        return True
    except Exception as exc:  # pragma: no cover - network
        log.warning("crm_webhook_failed", error=str(exc))
        return False
