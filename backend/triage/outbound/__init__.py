"""Outbound email delivery (sending the reviewed reply back to the sender)."""
from .smtp_sender import can_send_via_smtp, send_reply

__all__ = ["send_reply", "can_send_via_smtp"]
