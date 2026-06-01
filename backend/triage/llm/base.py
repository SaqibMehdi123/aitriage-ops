"""Provider-agnostic types and the Provider protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Literal, Protocol, TypedDict


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    raw: Any = field(default=None, repr=False)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMError(Exception):
    """Raised when a model call fails after retries (or is misconfigured)."""


# Transient errors worth retrying (rate limits, timeouts, 5xx). Providers map
# their own exception types onto this so the wrapper's retry policy stays generic.
class LLMTransientError(LLMError):
    pass


class Provider(Protocol):
    name: str

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        json_mode: bool = False,
        timeout: float = 30.0,
    ) -> LLMResponse: ...

    def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 30.0,
    ) -> Iterator[str]: ...
