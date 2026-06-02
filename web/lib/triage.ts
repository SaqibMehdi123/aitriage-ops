// Typed client functions over the FastAPI backend. All calls attach the
// Supabase access token via apiFetch (see lib/api.ts).
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type {
  Analytics,
  AuditEntry,
  Draft,
  EmailDetail,
  KnowledgeDoc,
  MailAccount,
  Member,
  OrgSettings,
  QueueResponse,
  Rule,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function qs(params: Record<string, string | number | boolean | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "" && v !== false) sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

// ── Emails / queue ──────────────────────────────────────────────────────
export function listEmails(filters: {
  status?: string;
  category?: string;
  urgency?: string;
  q?: string;
  mine?: boolean;
  limit?: number;
  offset?: number;
} = {}): Promise<QueueResponse> {
  return apiFetch<QueueResponse>(`/emails${qs(filters)}`);
}

export function getEmail(id: string): Promise<EmailDetail> {
  return apiFetch<EmailDetail>(`/emails/${id}`);
}

export function getDraft(id: string): Promise<Draft & { draft_id: string | null }> {
  return apiFetch(`/emails/${id}/draft`);
}

export function regenerateDraft(id: string): Promise<{ job_id: string }> {
  return apiFetch(`/emails/${id}/draft/regenerate`, { method: "POST" });
}

export function sendEmail(id: string, body: string, logToCrm = false): Promise<{ status: string }> {
  return apiFetch(`/emails/${id}/send`, {
    method: "POST",
    body: JSON.stringify({ body, log_to_crm: logToCrm }),
  });
}

export function assignEmail(id: string, assignee_id: string | null): Promise<unknown> {
  return apiFetch(`/emails/${id}/assign`, {
    method: "POST",
    body: JSON.stringify({ assignee_id }),
  });
}

export function ingestEmail(payload: {
  message_id: string;
  from_address: string;
  subject?: string;
  body?: string;
}): Promise<{ email_id: string; created: boolean }> {
  return apiFetch(`/emails/ingest`, {
    method: "POST",
    body: JSON.stringify({ email: payload }),
  });
}

// ── Streaming draft (SSE over fetch so we can attach the auth header) ──────
export async function streamDraft(
  id: string,
  onToken: (text: string) => void,
  onMeta?: (meta: { draft_id: string; sources: unknown[] }) => void,
): Promise<void> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const res = await fetch(`${API_BASE}/emails/${id}/draft/stream`, {
    headers: { Authorization: `Bearer ${session?.access_token ?? ""}` },
  });
  if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const events = buf.split("\n\n");
    buf = events.pop() ?? "";
    for (const evt of events) {
      const lines = evt.split("\n");
      const eventType = lines.find((l) => l.startsWith("event:"))?.slice(6).trim();
      const dataLine = lines.find((l) => l.startsWith("data:"))?.slice(5).trim() ?? "";
      if (eventType === "meta") {
        try {
          onMeta?.(JSON.parse(dataLine));
        } catch {
          /* ignore */
        }
      } else if (eventType === "error") {
        throw new Error(dataLine);
      } else if (!eventType) {
        // default message event = a token; unescape newlines
        onToken(dataLine.replace(/\\n/g, "\n"));
      }
    }
  }
}

// ── Members / rules / knowledge ───────────────────────────────────────────
export function listMembers(): Promise<Member[]> {
  return apiFetch<Member[]>(`/members`);
}

export function listRules(): Promise<Rule[]> {
  return apiFetch<Rule[]>(`/rules`);
}
export function createRule(rule: Partial<Rule>): Promise<Rule> {
  return apiFetch(`/rules`, { method: "POST", body: JSON.stringify(rule) });
}
export function updateRule(id: string, rule: Partial<Rule>): Promise<Rule> {
  return apiFetch(`/rules/${id}`, { method: "PUT", body: JSON.stringify(rule) });
}
export function deleteRule(id: string): Promise<unknown> {
  return apiFetch(`/rules/${id}`, { method: "DELETE" });
}

export function listKnowledge(): Promise<KnowledgeDoc[]> {
  return apiFetch<KnowledgeDoc[]>(`/knowledge`);
}
export function uploadKnowledgeText(title: string, content: string): Promise<{ doc_id: string }> {
  return apiFetch(`/knowledge/text`, { method: "POST", body: JSON.stringify({ title, content }) });
}
export function deleteKnowledge(id: string): Promise<unknown> {
  return apiFetch(`/knowledge/${id}`, { method: "DELETE" });
}

// ── Analytics / audit ─────────────────────────────────────────────────────
export function getAnalytics(days = 30): Promise<Analytics> {
  return apiFetch<Analytics>(`/analytics${qs({ days })}`);
}
export function getAudit(limit = 30): Promise<AuditEntry[]> {
  return apiFetch<AuditEntry[]>(`/audit${qs({ limit })}`);
}

// ── Mailbox accounts ──────────────────────────────────────────────────────
export function listAccounts(): Promise<MailAccount[]> {
  return apiFetch<MailAccount[]>(`/accounts`);
}
export function connectImap(body: {
  host: string;
  port: number;
  username: string;
  password: string;
}): Promise<MailAccount> {
  return apiFetch(`/accounts/connect/imap`, { method: "POST", body: JSON.stringify(body) });
}
export function syncAccount(id: string): Promise<unknown> {
  return apiFetch(`/accounts/${id}/sync`, { method: "POST" });
}
export function disconnectAccount(id: string): Promise<unknown> {
  return apiFetch(`/accounts/${id}`, { method: "DELETE" });
}

// ── Org settings (privacy) ────────────────────────────────────────────────
export function getOrgSettings(): Promise<OrgSettings> {
  return apiFetch<OrgSettings>(`/settings`);
}
export function updateOrgSettings(s: OrgSettings): Promise<OrgSettings> {
  return apiFetch(`/settings`, { method: "PUT", body: JSON.stringify(s) });
}
