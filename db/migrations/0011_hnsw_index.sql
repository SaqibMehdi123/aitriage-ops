-- 0011 — Switch the knowledge-chunk vector index from ivfflat to HNSW.
-- ivfflat needs many rows (and enough probes) to return complete results; on a
-- small knowledge base it can return zero neighbours, silently breaking RAG.
-- HNSW is robust across small and large datasets and needs no training data.

DROP INDEX IF EXISTS knowledge_chunks_embedding_idx;

CREATE INDEX knowledge_chunks_embedding_idx
    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
