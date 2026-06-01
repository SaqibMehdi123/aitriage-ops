"""Mailbox connectors. Each maps a provider's API onto InboundEmail and shares
the OAuth token-bundle shape. The ingestion service and worker treat them
uniformly via `get_connector`.
"""
from __future__ import annotations

from .base import TokenBundle
from .gmail import GmailConnector
from .graph import GraphConnector
from .imap import ImapConnector


def get_connector(provider: str):
    if provider == "gmail":
        return GmailConnector()
    if provider == "outlook":
        return GraphConnector()
    if provider == "imap":
        return ImapConnector()
    raise ValueError(f"Unknown mail provider: {provider!r}")


__all__ = ["TokenBundle", "GmailConnector", "GraphConnector", "ImapConnector", "get_connector"]
