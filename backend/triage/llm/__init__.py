"""Pluggable LLM access.

All model calls in the system go through `LLM` (the wrapper) — never a provider
SDK directly. The wrapper enforces timeouts, retries, model routing
(fast vs smart), structured-output validation, and Langfuse tracing in one
place, so swapping providers or models is a config change.
"""
from .base import ChatMessage, LLMResponse, LLMError
from .wrapper import LLM, get_llm

__all__ = ["LLM", "get_llm", "ChatMessage", "LLMResponse", "LLMError"]
