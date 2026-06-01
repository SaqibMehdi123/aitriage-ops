"""Split documents into overlapping chunks for embedding/retrieval.

Paragraph-aware: prefers to break on blank lines, falling back to hard slicing
for very long paragraphs. Overlap preserves context across chunk boundaries.
"""
from __future__ import annotations

import re

_WS = re.compile(r"[ \t]+")


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(_WS.sub(" ", line).rstrip() for line in text.split("\n")).strip()


def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    text = _normalize(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > chunk_size:
            # Flush current, then hard-slice the oversized paragraph.
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i : i + chunk_size].strip())
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            chunks.append(current.strip())
            # Carry the tail of the previous chunk for context overlap.
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{para}".strip() if tail else para

    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c]
