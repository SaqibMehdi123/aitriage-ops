"""Normalised inbound-email shape shared by all providers and the webhook."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InboundEmail(BaseModel):
    """A provider-agnostic email ready for ingestion. Connectors (Gmail/Graph/
    IMAP) and the webhook all map their payloads onto this."""

    message_id: str = Field(..., description="Provider message id — idempotency key")
    thread_id: str | None = None
    from_address: str
    to_address: str | None = None
    subject: str | None = None
    body: str | None = Field(default=None, description="Raw body (HTML or plain)")
    received_at: datetime | None = None
