-- 0007 — Align the knowledge embedding dimension with the free default.
-- The default embedding path (hash / fastembed bge-small) is 384-dim. The
-- initial schema used 1536 (OpenAI). The table is empty at this point, so we
-- can safely drop the index, change the column type, and recreate the index.
-- If you switch to OpenAI embeddings (1536), change this back and re-embed.

DROP INDEX IF EXISTS knowledge_chunks_embedding_idx;

ALTER TABLE knowledge_chunks
    ALTER COLUMN embedding TYPE vector(384);

CREATE INDEX knowledge_chunks_embedding_idx
    ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
