"""Gmail connector — OAuth 2.0 (authorization code) + polling via the REST API.

Uses plain httpx against Google's OAuth and Gmail endpoints (no heavyweight
google client libraries). Polling lists messages newer than the account
watermark; a Pub/Sub push subscription is a later optimisation. Scopes are
least-privilege: read messages now, send added in Module 5.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from ...config import get_settings
from ...logging import get_logger
from ..schemas import InboundEmail
from .base import TokenBundle

log = get_logger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


class GmailConnector:
    provider = "gmail"

    def __init__(self) -> None:
        self.settings = get_settings()

    # -- OAuth ------------------------------------------------------------
    def build_auth_url(self, state: str) -> str:
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",      # request a refresh token
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        return str(httpx.URL(AUTH_URL, params=params))

    def exchange_code(self, code: str) -> TokenBundle:
        data = {
            "code": code,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "redirect_uri": self.settings.google_oauth_redirect_uri,
            "grant_type": "authorization_code",
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(TOKEN_URL, data=data)
            resp.raise_for_status()
            return TokenBundle.from_token_response(resp.json())

    def refresh(self, bundle: TokenBundle) -> TokenBundle:
        if not bundle.refresh_token:
            raise RuntimeError("No refresh token available for Gmail account.")
        data = {
            "refresh_token": bundle.refresh_token,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "grant_type": "refresh_token",
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(TOKEN_URL, data=data)
            resp.raise_for_status()
            return TokenBundle.from_token_response(resp.json(), prev_refresh=bundle.refresh_token)

    def get_email_address(self, bundle: TokenBundle) -> str:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{API_BASE}/profile", headers=self._auth(bundle))
            resp.raise_for_status()
            return resp.json().get("emailAddress", "")

    # -- Fetch ------------------------------------------------------------
    def fetch_new(self, bundle: TokenBundle, since: datetime | None, *, max_results: int = 25) -> list[InboundEmail]:
        query = "in:inbox"
        if since:
            query += f" after:{int(since.timestamp())}"
        with httpx.Client(timeout=30) as client:
            headers = self._auth(bundle)
            listing = client.get(
                f"{API_BASE}/messages",
                headers=headers,
                params={"q": query, "maxResults": max_results},
            )
            listing.raise_for_status()
            ids = [m["id"] for m in listing.json().get("messages", [])]

            emails: list[InboundEmail] = []
            for mid in ids:
                detail = client.get(
                    f"{API_BASE}/messages/{mid}",
                    headers=headers,
                    params={"format": "full"},
                )
                detail.raise_for_status()
                emails.append(self._parse_message(detail.json()))
        return emails

    # -- parsing ----------------------------------------------------------
    @staticmethod
    def _auth(bundle: TokenBundle) -> dict:
        return {"Authorization": f"Bearer {bundle.access_token}"}

    def _parse_message(self, msg: dict) -> InboundEmail:
        payload = msg.get("payload", {})
        headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
        body = self._extract_body(payload)
        received = None
        if msg.get("internalDate"):
            received = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=timezone.utc)
        elif headers.get("date"):
            try:
                received = parsedate_to_datetime(headers["date"])
            except Exception:
                received = None
        return InboundEmail(
            message_id=headers.get("message-id") or msg["id"],
            thread_id=msg.get("threadId"),
            from_address=headers.get("from", ""),
            to_address=headers.get("to"),
            subject=headers.get("subject"),
            body=body,
            received_at=received,
        )

    def _extract_body(self, payload: dict) -> str:
        """Walk MIME parts, preferring text/plain, falling back to text/html."""
        plain, html = None, None

        def walk(part: dict) -> None:
            nonlocal plain, html
            mime = part.get("mimeType", "")
            data = part.get("body", {}).get("data")
            if data and mime == "text/plain" and plain is None:
                plain = self._b64(data)
            elif data and mime == "text/html" and html is None:
                html = self._b64(data)
            for sub in part.get("parts", []) or []:
                walk(sub)

        walk(payload)
        return plain or html or ""

    @staticmethod
    def _b64(data: str) -> str:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
