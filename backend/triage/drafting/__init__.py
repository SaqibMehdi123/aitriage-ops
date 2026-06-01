"""Reply drafting (Module 5).

Composes a context-aware reply from the email thread plus knowledge-base chunks
retrieved via RAG, records the cited sources, and can stream the output
token-by-token to the UI. The human reviews and sends (Module 7).
"""
from .service import draft_for_email, stream_draft

__all__ = ["draft_for_email", "stream_draft"]
