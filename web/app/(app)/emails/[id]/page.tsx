"use client";

import { use, useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  assignEmail,
  getEmail,
  listMembers,
  sendEmail,
  streamDraft,
} from "@/lib/triage";
import type { EmailDetail, Member } from "@/lib/types";
import { Avatar, CategoryChip, Icon, Spinner, UrgencyBadge } from "@/components/ui";

export default function EmailDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const [data, setData] = useState<EmailDetail | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [body, setBody] = useState("");
  const [sources, setSources] = useState<{ title: string | null; source: string | null }[]>([]);
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [d, m] = await Promise.all([getEmail(id), listMembers().catch(() => [])]);
      setData(d);
      setMembers(m);
      setBody(d.draft?.body ?? "");
      setSources(d.draft?.sources ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function regenerate() {
    setStreaming(true);
    setError(null);
    setBody("");
    setSources([]);
    try {
      await streamDraft(
        id,
        (tok) => setBody((b) => b + tok),
        (meta) => setSources((meta.sources as { title: string | null; source: string | null }[]) ?? []),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draft generation failed");
    } finally {
      setStreaming(false);
    }
  }

  async function doSend(logToCrm: boolean) {
    setSending(true);
    setError(null);
    try {
      await sendEmail(id, body, logToCrm);
      setNotice(logToCrm ? "Sent and logged to CRM." : "Sent.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Send failed");
    } finally {
      setSending(false);
    }
  }

  async function reassign(assignee_id: string) {
    try {
      await assignEmail(id, assignee_id || null);
      setData((d) => (d ? { ...d, assignee_id: assignee_id || null } : d));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reassign failed");
    }
  }

  if (loading) {
    return <div className="p-margin-desktop"><Spinner label="Loading email…" /></div>;
  }
  if (!data) {
    return <div className="p-margin-desktop text-error">{error ?? "Not found"}</div>;
  }

  const cls = data.classification;
  const alreadySent = data.status === "sent";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-16 px-margin-desktop border-b border-outline-variant bg-surface flex items-center justify-between shrink-0">
        <div className="flex items-center gap-md min-w-0">
          <button onClick={() => router.push("/queue")} className="p-xs hover:bg-surface-container rounded text-on-surface-variant">
            <Icon name="arrow_back" />
          </button>
          <h2 className="text-title-lg text-on-surface truncate max-w-xl">{data.subject || "(no subject)"}</h2>
        </div>
        <div className="flex items-center gap-sm">
          {cls && (
            <span className="text-label-sm text-secondary bg-secondary-fixed px-sm py-unit rounded-full">
              {Math.round(cls.confidence * 100)}% confidence
            </span>
          )}
          <span className="text-label-sm text-on-surface-variant bg-surface-container-high px-sm py-unit rounded-full capitalize">
            {data.status}
          </span>
        </div>
      </header>

      {(error || notice) && (
        <div className={`px-margin-desktop py-sm text-body-sm ${error ? "bg-error-container text-on-error-container" : "bg-secondary-fixed text-on-secondary-fixed"}`}>
          {error || notice}
        </div>
      )}

      {/* Two-pane */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden p-margin-desktop gap-lg">
        {/* Left: conversation */}
        <div className="lg:w-3/5 bg-surface-container-lowest border border-outline-variant rounded-xl flex flex-col overflow-hidden">
          <div className="px-lg py-md border-b border-outline-variant bg-surface-bright shrink-0">
            <h3 className="text-title-lg">Conversation</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-lg flex flex-col gap-lg">
            {(data.thread.length ? data.thread : [{ from_address: data.from_address, subject: data.subject, body_clean: data.body_clean, received_at: data.received_at }]).map((m, i) => (
              <div key={i} className="flex flex-col gap-xs max-w-3xl">
                <div className="flex items-center gap-sm">
                  <Avatar name={m.from_address} className="w-8 h-8" />
                  <span className="text-label-md text-on-surface">{m.from_address}</span>
                  {m.received_at && (
                    <span className="text-label-sm text-on-surface-variant">{new Date(m.received_at).toLocaleString()}</span>
                  )}
                </div>
                <div className="bg-surface-container-low p-md rounded-lg rounded-tl-none border border-surface-container-highest text-on-surface text-body-md whitespace-pre-wrap">
                  {m.body_clean || "(no content)"}
                </div>
              </div>
            ))}
            {cls && (
              <div className="flex items-center gap-md px-md">
                <div className="h-px bg-outline-variant flex-1" />
                <span className="text-label-sm text-on-surface-variant flex items-center gap-xs">
                  <Icon name="smart_toy" className="text-[14px]" /> AI categorised as
                  <CategoryChip category={cls.category} /> · <UrgencyBadge urgency={cls.urgency} />
                </span>
                <div className="h-px bg-outline-variant flex-1" />
              </div>
            )}
          </div>
        </div>

        {/* Right: AI draft */}
        <div className="lg:w-2/5 flex flex-col gap-md min-h-0">
          {/* Metadata */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shrink-0">
            <div className="flex items-center justify-between mb-sm">
              <div className="flex items-center gap-sm">
                <Icon name="auto_awesome" className="text-primary" />
                <span className="text-label-md text-on-surface">
                  {streaming ? "Generating draft…" : body ? "Suggested draft" : "No draft yet"}
                </span>
              </div>
              <select
                value={data.assignee_id ?? ""}
                onChange={(e) => reassign(e.target.value)}
                className="text-label-sm border border-outline-variant rounded px-sm py-unit bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Unassigned</option>
                {members.map((m) => (
                  <option key={m.user_id} value={m.user_id}>{m.full_name || m.email}</option>
                ))}
              </select>
            </div>
            {sources.length > 0 && (
              <div className="flex items-center gap-sm flex-wrap mt-sm">
                <span className="text-label-sm text-on-surface-variant">Sources:</span>
                {sources.map((s, i) => (
                  <span key={i} className="text-label-sm bg-surface-container px-sm py-unit rounded border border-outline-variant text-on-surface flex items-center gap-xs">
                    <Icon name="description" className="text-[14px]" /> {s.title || s.source || "Source"}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Editor */}
          <div className="flex-1 min-h-[240px] bg-surface-container-lowest border border-outline-variant rounded-xl flex flex-col overflow-hidden focus-within:ring-2 focus-within:ring-primary">
            <textarea
              ref={textareaRef}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled={streaming || alreadySent}
              placeholder="Draft your reply here, or click Regenerate to let the AI draft one…"
              className="flex-1 w-full p-md resize-none border-none focus:ring-0 text-body-md text-on-surface bg-transparent"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between shrink-0">
            <div className="flex gap-sm">
              <button
                onClick={regenerate}
                disabled={streaming || sending || alreadySent}
                className="px-md py-sm rounded border border-outline-variant text-on-surface text-label-md hover:bg-surface-container transition-colors flex items-center gap-xs disabled:opacity-60"
              >
                <Icon name="refresh" className="text-[18px]" /> {body ? "Regenerate" : "Generate"}
              </button>
            </div>
            <div className="flex gap-sm">
              <button
                onClick={() => doSend(false)}
                disabled={sending || streaming || !body || alreadySent}
                className="px-md py-sm rounded border border-primary text-primary text-label-md hover:bg-primary-fixed-dim transition-colors disabled:opacity-60"
              >
                Send
              </button>
              <button
                onClick={() => doSend(true)}
                disabled={sending || streaming || !body || alreadySent}
                className="px-md py-sm rounded bg-primary text-on-primary text-label-md hover:bg-primary-container transition-colors shadow-sm flex items-center gap-xs disabled:opacity-60"
              >
                <Icon name="send" className="text-[18px]" /> Send &amp; log to CRM
              </button>
            </div>
          </div>
          {alreadySent && <p className="text-label-sm text-tertiary">This email has been sent.</p>}
        </div>
      </div>
    </div>
  );
}
