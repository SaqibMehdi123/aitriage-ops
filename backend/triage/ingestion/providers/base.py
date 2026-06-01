"""Shared types for mailbox connectors."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TokenBundle:
    """OAuth tokens persisted (encrypted) in email_accounts.oauth_tokens."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    scope: str | None = None
    expires_at: float | None = None  # epoch seconds

    @classmethod
    def from_token_response(cls, data: dict, *, prev_refresh: str | None = None) -> "TokenBundle":
        expires_in = data.get("expires_in")
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token") or prev_refresh,
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope"),
            expires_at=(time.time() + float(expires_in)) if expires_in else None,
        )

    @property
    def is_expired(self) -> bool:
        # Refresh a minute early to avoid races on the edge of expiry.
        return self.expires_at is not None and time.time() >= (self.expires_at - 60)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "scope": self.scope,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenBundle":
        return cls(**data)


def to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
