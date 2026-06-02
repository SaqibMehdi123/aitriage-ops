// Shared API types mirroring the FastAPI responses.

export type EmailStatus = "new" | "classified" | "drafted" | "sent" | "review";
export type Urgency = "low" | "normal" | "high";

export interface QueueItem {
  id: string;
  from_address: string;
  subject: string | null;
  status: EmailStatus;
  category: string | null;
  confidence: number | null;
  urgency: Urgency | null;
  assignee_id: string | null;
  assignee_name: string | null;
  has_draft: boolean;
  received_at: string | null;
}

export interface QueueResponse {
  items: QueueItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface Classification {
  category: string;
  confidence: number;
  urgency: Urgency;
  rationale?: string;
  model?: string;
}

export interface DraftSource {
  chunk_id: string;
  doc_id: string;
  title: string | null;
  source: string | null;
  score: number;
}

export interface Draft {
  id: string;
  body: string;
  status: "draft" | "edited" | "sent" | "discarded";
  sources: DraftSource[];
  model?: string;
}

export interface ThreadMessage {
  from_address: string;
  subject: string | null;
  body_clean: string | null;
  received_at: string | null;
}

export interface EmailDetail {
  id: string;
  from_address: string;
  to_address: string | null;
  subject: string | null;
  body_clean: string | null;
  status: EmailStatus;
  received_at: string | null;
  assignee_id: string | null;
  classification: Classification | null;
  draft: Draft | null;
  thread: ThreadMessage[];
}

export interface Member {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
}

export interface RuleCondition {
  field: string;
  op?: string;
  value: unknown;
}

export interface Rule {
  id: string;
  name: string | null;
  priority: number;
  conditions: { all?: RuleCondition[]; any?: RuleCondition[] };
  assignee_id: string | null;
  crm_action: Record<string, unknown> | null;
  is_active: boolean;
}

export interface KnowledgeDoc {
  id: string;
  title: string;
  source: string | null;
  status: string;
  created_at: string | null;
}

export interface OrgSettings {
  pii_redaction: boolean;
  retention_days: number | null;
}

export interface MailAccount {
  id: string;
  provider: string;
  email_address: string;
  status: string;
  last_synced_at: string | null;
}

export interface Analytics {
  range_days: number;
  summary: {
    emails_processed: number;
    median_response_seconds: number | null;
    hours_saved: number;
    draft_acceptance_rate: number | null;
    llm_tokens: number;
    failed_jobs: number;
  };
  volume: { date: string; ai_handled: number; human_required: number }[];
  category_mix: { category: string; count: number; pct: number }[];
}

export interface AuditEntry {
  id: string;
  actor_email: string | null;
  action: string;
  entity: Record<string, unknown>;
  created_at: string | null;
}
