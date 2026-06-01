-- 0004 — Classification results and AI reply drafts.

CREATE TABLE classifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email_id        UUID NOT NULL REFERENCES emails(id),
    category        TEXT NOT NULL,                -- Support | Sales | Billing | Spam | Other
    confidence      NUMERIC(4,3) NOT NULL,        -- 0.000–1.000
    urgency         urgency_level NOT NULL DEFAULT 'normal',
    model           TEXT,                         -- model + prompt version used
    rationale       TEXT,                         -- short model explanation (for audit)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);
-- One active classification per email (one-to-one per the schema).
CREATE UNIQUE INDEX classifications_email_unique
    ON classifications (email_id) WHERE deleted_at IS NULL;
CREATE INDEX classifications_org_category_idx
    ON classifications (organization_id, category) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_classifications_updated_at
    BEFORE UPDATE ON classifications
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE drafts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email_id        UUID NOT NULL REFERENCES emails(id),
    body            TEXT NOT NULL,                -- generated reply
    sources         JSONB NOT NULL DEFAULT '[]',  -- cited KB chunk ids
    status          draft_status NOT NULL DEFAULT 'draft',
    model           TEXT,
    sent_by         UUID REFERENCES users(id),    -- who sent it (if sent)
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX drafts_email_idx ON drafts (email_id) WHERE deleted_at IS NULL;
CREATE INDEX drafts_org_status_idx ON drafts (organization_id, status) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_drafts_updated_at
    BEFORE UPDATE ON drafts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
