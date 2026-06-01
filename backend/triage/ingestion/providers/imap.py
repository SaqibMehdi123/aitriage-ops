"""IMAP fallback connector — for providers without OAuth, using an app password.

Credentials (host/port/username/password) are stored in the same encrypted
oauth_tokens column as a JSON bundle. Fetches recent messages and normalises
them to InboundEmail. Uses the stdlib (imaplib + email), no extra deps.
"""
from __future__ import annotations

import email
import imaplib
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

from ...logging import get_logger
from ..schemas import InboundEmail

log = get_logger(__name__)


class ImapConnector:
    provider = "imap"

    def verify(self, creds: dict) -> str:
        """Test login; returns the connected address. Raises on failure."""
        conn = self._connect(creds)
        try:
            conn.select("INBOX", readonly=True)
        finally:
            self._logout(conn)
        return creds.get("username", "")

    def fetch_new(self, creds: dict, since: datetime | None, *, max_results: int = 25) -> list[InboundEmail]:
        conn = self._connect(creds)
        emails: list[InboundEmail] = []
        try:
            conn.select("INBOX", readonly=True)
            criteria = ["ALL"]
            if since:
                criteria = ["SINCE", since.strftime("%d-%b-%Y")]
            typ, data = conn.search(None, *criteria)
            if typ != "OK":
                return []
            ids = data[0].split()[-max_results:]  # most recent N
            for num in ids:
                typ, msg_data = conn.fetch(num, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                emails.append(self._parse(email.message_from_bytes(raw)))
        finally:
            self._logout(conn)
        return emails

    # -- internals --------------------------------------------------------
    @staticmethod
    def _connect(creds: dict) -> imaplib.IMAP4_SSL:
        conn = imaplib.IMAP4_SSL(creds["host"], int(creds.get("port", 993)))
        conn.login(creds["username"], creds["password"])
        return conn

    @staticmethod
    def _logout(conn: imaplib.IMAP4_SSL) -> None:
        try:
            conn.close()
        except Exception:
            pass
        try:
            conn.logout()
        except Exception:
            pass

    def _parse(self, msg: email.message.Message) -> InboundEmail:
        def hdr(name: str) -> str | None:
            value = msg.get(name)
            return str(make_header(decode_header(value))) if value else None

        received = None
        if msg.get("Date"):
            try:
                received = parsedate_to_datetime(msg["Date"])
            except Exception:
                received = None
        return InboundEmail(
            message_id=hdr("Message-ID") or f"imap-{hash(msg.as_string())}",
            thread_id=hdr("References") or hdr("In-Reply-To"),
            from_address=hdr("From") or "",
            to_address=hdr("To"),
            subject=hdr("Subject"),
            body=self._body(msg),
            received_at=received or datetime.now(timezone.utc),
        )

    @staticmethod
    def _body(msg: email.message.Message) -> str:
        plain, html = None, None
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if part.get("Content-Disposition", "").startswith("attachment"):
                    continue
                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                except Exception:
                    continue
                if ctype == "text/plain" and plain is None:
                    plain = text
                elif ctype == "text/html" and html is None:
                    html = text
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                plain = payload.decode(charset, errors="replace")
        return plain or html or ""
