-- 0010 — Per-tenant privacy controls and LLM usage/cost tracking (Module 9).

CREATE TABLE org_settings (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    pii_redaction   BOOLEAN NOT NULL DEFAULT false,   -- redact PII before any LLM call
    retention_days  INT,                               -- NULL = keep indefinitely
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_org_settings_updated_at
    BEFORE UPDATE ON org_settings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- One row per model call, for the cost/usage dashboard and per-tenant metering.
CREATE TABLE llm_usage (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID REFERENCES organizations(id),
    kind              TEXT,                  -- classify | draft | other
    model             TEXT,
    prompt_tokens     INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX llm_usage_org_created_idx ON llm_usage (organization_id, created_at DESC);
