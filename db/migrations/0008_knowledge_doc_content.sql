-- 0008 — Store the raw extracted text on the document so the (async) embedding
-- worker can read it. For large files this would point at object storage via
-- storage_path instead; raw_content keeps v1 simple.

ALTER TABLE knowledge_docs ADD COLUMN raw_content TEXT;
