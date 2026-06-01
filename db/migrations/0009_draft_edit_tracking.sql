-- 0009 — Track whether a sent draft was edited by the human before sending.
-- Powers the "drafts sent with no edit" quality metric (PRD success metric).

ALTER TABLE drafts ADD COLUMN was_edited BOOLEAN NOT NULL DEFAULT false;
