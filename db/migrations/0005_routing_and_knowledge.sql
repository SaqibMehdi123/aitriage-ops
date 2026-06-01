-- 0005 — Routing rules and the knowledge base (RAG).
-- Embedding dimension defaults to 1536 (OpenAI text-embedding-3-small). Groq
-- does not yet expose an embeddings endpoint, so embeddings are produced by the
-- configured EMBEDDING_PROVIDER (see README). Change vector(1536) here if you
-- switch to a model with a different dimensionality.

CREATE TABLE routing_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name            TEXT,
    priority        INT NOT NULL DEFAULT 100,     -- lower = evaluated first
    -- conditions: { all: [ {field, op, value}, ... ] } — category/urgency/keyword
    conditions      JSONB NOT NULL DEFAULT '{}',
    assignee_id     UUID REFERENCES users(id),    -- target teammate
    crm_action      JSONB,                        -- optional CRM log config
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX routing_rules_org_priority_idx
    ON routing_rules (organization_id, priority) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_routing_rules_updated_at
    BEFORE UPDATE ON routing_rules
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE knowledge_docs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    title           TEXT NOT NULL,
    source          TEXT,                         -- filename / URL
    storage_path    TEXT,                         -- object-storage key (S3-compatible)
    status          TEXT NOT NULL DEFAULT 'pending', -- pending | embedding | synced | error
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX knowledge_docs_org_idx ON knowledge_docs (organization_id) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_knowledge_docs_updated_at
    BEFORE UPDATE ON knowledge_docs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE knowledge_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    doc_id          UUID NOT NULL REFERENCES knowledge_docs(id),
    chunk_index     INT NOT NULL,
    content         TEXT NOT NULL,                -- chunk text
    embedding       vector(1536),                 -- pgvector embedding for retrieval
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX knowledge_chunks_org_doc_idx ON knowledge_chunks (organization_id, doc_id);
-- Approximate nearest-neighbour index for cosine similarity retrieval.
CREATE INDEX knowledge_chunks_embedding_idx
    ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE TRIGGER trg_knowledge_chunks_updated_at
    BEFORE UPDATE ON knowledge_chunks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
