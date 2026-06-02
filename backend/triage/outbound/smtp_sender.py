"""Send a reply over SMTP using a mailbox's stored IMAP/app-password creds.

For IMAP-connected mailboxes (e.g. Gmail with an app password) the same
credentials work for SMTP submission, so we can deliver the human-approved reply
back to the original sender. OAuth mailboxes (gmail/outlook) would instead use
the provider's send API with a send scope — not enabled here.
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr

from ..logging import get_logger

log = get_logger(__name__)


def can_send_via_smtp(provider: str, creds: dict) -> bool:
    return provider == "imap" and bool(creds.get("host") and creds.get("username") and creds.get("password"))


def _smtp_host(imap_host: str) -> str:
    # imap.gmail.com -> smtp.gmail.com; imap.<domain> -> smtp.<domain>
    return "smtp." + imap_host[len("imap."):] if imap_host.startswith("imap.") else imap_host


def send_reply(creds: dict, *, from_addr: str, to_addr: str, subject: str | None,
               body: str, in_reply_to: str | None = None) -> None:
    """Deliver a plain-text reply. Raises on failure so the caller can surface it."""
    recipient = parseaddr(to_addr)[1] or to_addr
    subj = subject or ""
    if not subj.lower().startswith("re:"):
        subj = f"Re: {subj}".strip()

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = recipient
    msg["Subject"] = subj
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)

    host = _smtp_host(creds["host"])
    context = ssl.create_default_context()
    with smtplib.SMTP(host, 587, timeout=30) as server:
        server.starttls(context=context)
        server.login(creds["username"], creds["password"])
        server.send_message(msg)
    log.info("smtp_reply_sent", to=recipient, host=host)
