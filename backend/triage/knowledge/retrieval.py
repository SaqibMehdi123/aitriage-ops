"""Top-k semantic retrieval over an organisation's knowledge chunks.

Org-scoped (multi-tenancy) cosine search via pgvector's `<=>` operator, with an
optional metadata filter. Returns chunks with a similarity score in [0,1] used
to ground reply drafts and to show citations in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config import get_settings
from ..db import connection
from .embeddings import get_embedder, to_pgvector


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    content: str
    score: float
    title: str | None = None
    source: str | None = None


def retrieve(
    organization_id: str,
    query: str,
    *,
    k: int | None = None,
    metadata_filter: dict | None = None,
) -> list[RetrievedChunk]:
    if not query.strip():
        return []
    k = k or get_settings().rag_top_k
    vec = to_pgvector(get_embedder().embed([query])[0])

    sql = [
        "SELECT c.id, c.doc_id, c.content, d.title, d.source,",
        "       1 - (c.embedding <=> %s::vector) AS score",
        "FROM knowledge_chunks c JOIN knowledge_docs d ON d.id = c.doc_id",
        "WHERE c.organization_id = %s AND c.deleted_at IS NULL AND d.deleted_at IS NULL",
    ]
    params: list = [vec, organization_id]
    for key, value in (metadata_filter or {}).items():
        sql.append("AND c.metadata ->> %s = %s")
        params += [key, str(value)]
    sql.append("ORDER BY c.embedding <=> %s::vector LIMIT %s")
    params += [vec, k]

    with connection() as conn:
        rows = conn.execute("\n".join(sql), params).fetchall()

    return [
        RetrievedChunk(
            chunk_id=str(r["id"]), doc_id=str(r["doc_id"]), content=r["content"],
            score=float(r["score"]), title=r.get("title"), source=r.get("source"),
        )
        for r in rows
    ]
