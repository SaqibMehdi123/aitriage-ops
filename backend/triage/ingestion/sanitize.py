"""Turn an untrusted raw email body into clean, model-safe text.

Email content is treated as hostile input (TRD security): it may contain HTML,
tracking junk, invisible characters, and deliberate prompt-injection attempts
("ignore previous instructions, you are now…"). This module:

  1. Extracts readable text from HTML (scripts/styles dropped).
  2. Strips invisible/zero-width and control characters often used to smuggle
     hidden instructions past a reviewer.
  3. Neutralises overt injection phrases by redacting them, and reports whether
     anything was found so the email can be flagged for human review.

This is defence-in-depth. The *primary* injection defence is structural: when
the cleaned body reaches the LLM (Modules 3/5) it is wrapped in explicit
delimiters and the system prompt instructs the model to treat it as data, never
as instructions. Sanitisation here reduces the attack surface; it is not a
substitute for that.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from bs4 import BeautifulSoup

# Zero-width and bidi/control characters frequently used to hide payloads.
# Built from explicit codepoints so no literal invisible characters live in the
# source: ZWSP, ZWNJ, ZWJ, LRM, RLM, bidi embeddings/overrides, word joiner,
# BOM/ZWNBSP, plus C0 control chars (keeping \t \n \r).
_INVISIBLE_CODEPOINTS = (
    [0x200B, 0x200C, 0x200D, 0x200E, 0x200F]
    + list(range(0x202A, 0x202F))  # bidi embeds/overrides + LRI/RLI/FSI/PDI region
    + [0x2060, 0xFEFF]
    + [c for c in range(0x00, 0x20) if c not in (0x09, 0x0A, 0x0D)]
)
_INVISIBLE = re.compile("[" + "".join(chr(c) for c in _INVISIBLE_CODEPOINTS) + "]")

# Overt prompt-injection patterns. Conservative — aimed at clear override
# attempts, not normal prose. Matched case-insensitively, line-anchored where
# sensible to limit false positives.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts|messages)", re.I),
    re.compile(r"disregard (all |the )?(previous|prior|above) (instructions|context)", re.I),
    re.compile(r"forget (everything|all previous|your instructions)", re.I),
    re.compile(r"you are now (a|an|acting as|in)\b", re.I),
    re.compile(r"new (instructions|system prompt|directive)\s*[:\-]", re.I),
    re.compile(r"\bsystem\s*prompt\b\s*[:\-]", re.I),
    # Inline role markers used to fake a chat turn inside the body.
    re.compile(r"^\s*(system|assistant|developer)\s*:", re.I | re.M),
    re.compile(r"<\s*/?\s*(system|assistant|instructions)\s*>", re.I),
]

_REDACTION = "[redacted: possible injected instruction]"


@dataclass
class SanitizedBody:
    text: str
    had_html: bool
    injection_suspected: bool
    redactions: int


def _html_to_text(raw: str) -> tuple[str, bool]:
    looks_html = bool(re.search(r"<[a-zA-Z/][^>]*>", raw))
    if not looks_html:
        return raw, False
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "head", "title", "meta", "link"]):
        tag.decompose()
    # Preserve some structure: line breaks for block elements.
    text = soup.get_text(separator="\n")
    return text, True


def _normalize_whitespace(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _INVISIBLE.sub("", text)
    # Collapse runs of blank lines / trailing spaces.
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip()


def _neutralize_injections(text: str) -> tuple[str, int]:
    count = 0

    def _sub(_m: re.Match) -> str:
        nonlocal count
        count += 1
        return _REDACTION

    for pat in _INJECTION_PATTERNS:
        text = pat.sub(_sub, text)
    return text, count


def sanitize_email_body(raw: str | None) -> SanitizedBody:
    """Main entry: raw body (HTML or plain) → cleaned, injection-neutralised text."""
    if not raw:
        return SanitizedBody(text="", had_html=False, injection_suspected=False, redactions=0)

    text, had_html = _html_to_text(raw)
    text = _normalize_whitespace(text)
    text, redactions = _neutralize_injections(text)

    return SanitizedBody(
        text=text,
        had_html=had_html,
        injection_suspected=redactions > 0,
        redactions=redactions,
    )
