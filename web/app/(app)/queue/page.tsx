"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { listEmails } from "@/lib/triage";
import type { QueueItem } from "@/lib/types";
import { Avatar, CategoryChip, Confidence, Icon, Spinner, StatusChip, UrgencyBadge } from "@/components/ui";

const CATEGORIES = ["Support", "Sales", "Billing", "Spam", "Other"];
const URGENCIES = ["high", "normal", "low"];
const STATUSES = ["new", "classified", "drafted", "review", "sent"];
const PAGE_SIZE = 25;

function QueueInner() {
  const router = useRouter();
  const params = useSearchParams();

  // Filters + paging live in the URL, so opening an email and pressing Back
  // returns to the exact same page and filters.
  const category = params.get("category") ?? "";
  const urgency = params.get("urgency") ?? "";
  const status = params.get("status") ?? "";
  const offset = Math.max(0, parseInt(params.get("offset") ?? "0", 10) || 0);

  const [items, setItems] = useState<QueueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function setParams(next: Record<string, string>, resetOffset = true) {
    const sp = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(next)) {
      if (v) sp.set(k, v);
      else sp.delete(k);
    }
    if (resetOffset && !("offset" in next)) sp.delete("offset");
    router.replace(`/queue?${sp.toString()}`, { scroll: false });
  }

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listEmails({ category, urgency, status, limit: PAGE_SIZE, offset });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [category, urgency, status, offset]);

  useEffect(() => {
    load();
  }, [load]);

  const Select = ({ value, onChange, placeholder, options }: {
    value: string; onChange: (v: string) => void; placeholder: string; options: string[];
  }) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-label-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary capitalize"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o} value={o} className="capitalize">{o}</option>
      ))}
    </select>
  );

  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);
  const canPrev = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  return (
    <div className="p-margin-mobile sm:p-margin-desktop max-w-container-max">
      <header className="mb-lg flex flex-col gap-md sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-display-lg">Triage Queue</h1>
          <p className="text-body-md text-on-surface-variant">Reviewing incoming support requests.</p>
        </div>
        <div className="flex items-center gap-sm">
          <button onClick={load}
            className="rounded border border-outline-variant px-md py-sm text-label-md hover:bg-surface-container transition-colors flex items-center gap-xs">
            <Icon name="refresh" className="text-[18px]" /> Refresh
          </button>
        </div>
      </header>

      <div className="flex flex-wrap gap-sm mb-md">
        <Select value={category} onChange={(v) => setParams({ category: v })} placeholder="Category" options={CATEGORIES} />
        <Select value={urgency} onChange={(v) => setParams({ urgency: v })} placeholder="Urgency" options={URGENCIES} />
        <Select value={status} onChange={(v) => setParams({ status: v })} placeholder="Status" options={STATUSES} />
      </div>

      {error && (
        <div className="mb-md rounded-lg border border-error-container bg-error-container text-on-error-container px-md py-sm text-body-sm">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-outline-variant bg-surface-container-lowest overflow-hidden">
        {/* Horizontal scroll so every column (incl. Assignee) stays readable on
            tablet/mobile instead of being squeezed off-screen. */}
        <div className="overflow-x-auto">
        <table className="w-full min-w-[920px] text-left">
          <thead>
            <tr className="border-b border-outline-variant text-label-sm text-on-surface-variant uppercase tracking-wide">
              <th className="px-lg py-md font-semibold">Sender</th>
              <th className="px-lg py-md font-semibold">Subject</th>
              <th className="px-lg py-md font-semibold">Category</th>
              <th className="px-lg py-md font-semibold">Urgency</th>
              <th className="px-lg py-md font-semibold">AI Confidence</th>
              <th className="px-lg py-md font-semibold">Status</th>
              <th className="px-lg py-md font-semibold">Assignee</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} onClick={() => router.push(`/emails/${it.id}`)}
                className="border-b border-surface-container-high last:border-0 hover:bg-surface-container-low cursor-pointer transition-colors">
                <td className="px-lg py-md">
                  <div className="flex items-center gap-sm">
                    <Avatar name={it.from_address} className="w-8 h-8" />
                    <span className="text-body-sm text-on-surface truncate max-w-[160px]">{it.from_address}</span>
                  </div>
                </td>
                <td className="px-lg py-md">
                  <div className="flex items-center gap-sm">
                    <span className="text-body-sm text-on-surface truncate max-w-[280px]">{it.subject || "(no subject)"}</span>
                    {it.has_draft && (
                      <span className="inline-flex items-center gap-xs text-label-sm text-primary">
                        <Icon name="auto_awesome" className="text-[14px]" /> draft
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-lg py-md"><CategoryChip category={it.category} /></td>
                <td className="px-lg py-md"><UrgencyBadge urgency={it.urgency} /></td>
                <td className="px-lg py-md"><Confidence value={it.confidence} /></td>
                <td className="px-lg py-md"><StatusChip status={it.status} /></td>
                <td className="px-lg py-md">
                  {it.assignee_name ? (
                    <div className="flex items-center gap-xs">
                      <Avatar name={it.assignee_name} className="w-7 h-7" />
                      <span className="text-body-sm text-on-surface-variant truncate max-w-[120px]">{it.assignee_name}</span>
                    </div>
                  ) : (
                    <span className="text-on-surface-variant text-label-sm">Unassigned</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>

        {loading &&<div className="px-lg py-xl flex justify-center"><Spinner label="Loading queue…" /></div>}

        {!loading && items.length === 0 && (
          <div className="px-lg py-xl flex flex-col items-center text-center gap-xs">
            <Icon name="done_all" className="text-[32px] text-on-surface-variant" />
            <p className="text-headline-sm">All caught up</p>
            <p className="text-body-sm text-on-surface-variant">
              No items match your current filters. Connect a mailbox in <em>Settings</em>, and new
              email will be triaged here automatically.
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between mt-md text-body-sm text-on-surface-variant">
          <span>Showing <strong className="text-on-surface">{from}–{to}</strong> of {total}</span>
          <div className="flex items-center gap-sm">
            <button
              disabled={!canPrev}
              onClick={() => setParams({ offset: String(Math.max(0, offset - PAGE_SIZE)) }, false)}
              className="rounded border border-outline-variant px-md py-sm text-label-md hover:bg-surface-container transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-xs"
            >
              <Icon name="chevron_left" className="text-[18px]" /> Prev
            </button>
            <button
              disabled={!canNext}
              onClick={() => setParams({ offset: String(offset + PAGE_SIZE) }, false)}
              className="rounded border border-outline-variant px-md py-sm text-label-md hover:bg-surface-container transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-xs"
            >
              Next <Icon name="chevron_right" className="text-[18px]" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function QueuePage() {
  return (
    <Suspense fallback={<div className="p-margin-mobile sm:p-margin-desktop"><Spinner label="Loading…" /></div>}>
      <QueueInner />
    </Suspense>
  );
}
