"""Microsoft Graph (Outlook/Microsoft 365) connector — OAuth 2.0 + polling.

Same shape as the Gmail connector, against the Microsoft identity platform and
Graph mail endpoints.
"""
from __future__ import annotations

from datetime import datetime

import httpx

from ...config import get_settings
from ...logging import get_logger
from ..schemas import InboundEmail
from .base import TokenBundle, to_utc

log = get_logger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["offline_access", "openid", "email", "Mail.Read"]


class GraphConnector:
    provider = "outlook"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._tenant = self.settings.ms_graph_tenant_id or "common"

    def _authority(self, leaf: str) -> str:
        return f"https://login.microsoftonline.com/{self._tenant}/oauth2/v2.0/{leaf}"

    # -- OAuth ------------------------------------------------------------
    def build_auth_url(self, state: str) -> str:
        params = {
            "client_id": self.settings.ms_graph_client_id,
            "response_type": "code",
            "redirect_uri": self.settings.google_oauth_redirect_uri.replace("google", "microsoft"),
            "response_mode": "query",
            "scope": " ".join(SCOPES),
            "state": state,
        }
        return str(httpx.URL(self._authority("authorize"), params=params))

    def exchange_code(self, code: str) -> TokenBundle:
        return self._token_request({
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.settings.google_oauth_redirect_uri.replace("google", "microsoft"),
        })

    def refresh(self, bundle: TokenBundle) -> TokenBundle:
        if not bundle.refresh_token:
            raise RuntimeError("No refresh token available for Outlook account.")
        return self._token_request(
            {"refresh_token": bundle.refresh_token, "grant_type": "refresh_token"},
            prev_refresh=bundle.refresh_token,
        )

    def _token_request(self, extra: dict, *, prev_refresh: str | None = None) -> TokenBundle:
        data = {
            "client_id": self.settings.ms_graph_client_id,
            "client_secret": self.settings.ms_graph_client_secret,
            "scope": " ".join(SCOPES),
            **extra,
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(self._authority("token"), data=data)
            resp.raise_for_status()
            return TokenBundle.from_token_response(resp.json(), prev_refresh=prev_refresh)

    def get_email_address(self, bundle: TokenBundle) -> str:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{GRAPH_BASE}/me", headers=self._auth(bundle))
            resp.raise_for_status()
            data = resp.json()
            return data.get("mail") or data.get("userPrincipalName", "")

    # -- Fetch ------------------------------------------------------------
    def fetch_new(self, bundle: TokenBundle, since: datetime | None, *, max_results: int = 25) -> list[InboundEmail]:
        params = {
            "$top": max_results,
            "$orderby": "receivedDateTime desc",
            "$select": "internetMessageId,conversationId,from,toRecipients,subject,body,receivedDateTime",
        }
        if since:
            params["$filter"] = f"receivedDateTime ge {to_utc(since).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{GRAPH_BASE}/me/messages", headers=self._auth(bundle), params=params)
            resp.raise_for_status()
            return [self._parse_message(m) for m in resp.json().get("value", [])]

    @staticmethod
    def _auth(bundle: TokenBundle) -> dict:
        return {"Authorization": f"Bearer {bundle.access_token}"}

    def _parse_message(self, m: dict) -> InboundEmail:
        from_addr = (m.get("from", {}) or {}).get("emailAddress", {}).get("address", "")
        to = m.get("toRecipients") or []
        to_addr = to[0]["emailAddress"]["address"] if to else None
        received = None
        if m.get("receivedDateTime"):
            received = datetime.fromisoformat(m["receivedDateTime"].replace("Z", "+00:00"))
        return InboundEmail(
            message_id=m.get("internetMessageId") or m["id"],
            thread_id=m.get("conversationId"),
            from_address=from_addr,
            to_address=to_addr,
            subject=m.get("subject"),
            body=(m.get("body", {}) or {}).get("content"),
            received_at=received,
        )
