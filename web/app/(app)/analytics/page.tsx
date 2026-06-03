"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getAnalytics, getAudit } from "@/lib/triage";
import type { Analytics, AuditEntry } from "@/lib/types";
import { Icon, Spinner } from "@/components/ui";

const DONUT_COLORS = ["#d97706", "#0f766e", "#57534e", "#b45309", "#a8a29e"];

function fmtDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m < 60 ? `${m}m ${s}s` : `${Math.floor(m / 60)}h ${m % 60}m`;
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-lg">
      <div className="flex items-center justify-between mb-sm">
        <span className="text-label-sm text-on-surface-variant uppercase tracking-wide">{label}</span>
        <Icon name={icon} className="text-on-surface-variant text-[20px]" />
      </div>
      <p className="text-display-lg text-on-surface">{value}</p>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [a, au] = await Promise.all([getAnalytics(days), getAudit(20).catch(() => [])]);
      setData(a);
      setAudit(au);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !data) return <div className="p-margin-desktop"><Spinner label="Loading analytics…" /></div>;

  const s = data?.summary;
  const donut = (data?.category_mix ?? []).map((c) => ({ name: c.category, value: c.count }));

  return (
    <div className="p-margin-desktop max-w-container-max">
      <header className="mb-lg flex items-start justify-between">
        <div>
          <h1 className="text-display-lg">Analytics Overview</h1>
          <p className="text-body-md text-on-surface-variant">Performance metrics across all triage workflows.</p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </header>

      {error && (
        <div className="mb-md rounded-lg border border-error-container bg-error-container text-on-error-container px-md py-sm text-body-sm">{error}</div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md mb-lg">
        <StatCard label="Emails processed" value={String(s?.emails_processed ?? 0)} icon="mail" />
        <StatCard label="Median response" value={fmtDuration(s?.median_response_seconds ?? null)} icon="schedule" />
        <StatCard label="Hours saved" value={`${s?.hours_saved ?? 0}h`} icon="schedule_send" />
        <StatCard label="Draft acceptance" value={s?.draft_acceptance_rate != null ? `${Math.round(s.draft_acceptance_rate * 100)}%` : "—"} icon="thumb_up" />
        <StatCard label="AI tokens used" value={(s?.llm_tokens ?? 0).toLocaleString()} icon="toll" />
        <StatCard label="Failed jobs" value={String(s?.failed_jobs ?? 0)} icon="error" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg">
        {/* Volume line */}
        <div className="lg:col-span-2 rounded-xl border border-outline-variant bg-surface-container-lowest p-lg">
          <h2 className="text-headline-sm mb-xs">Processing Volume</h2>
          <p className="text-body-sm text-on-surface-variant mb-md">AI-handled vs human-required over time</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.volume ?? []} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#57534e" }} tickFormatter={(d) => String(d).slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: "#57534e" }} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="ai_handled" name="AI handled" stroke="#d97706" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="human_required" name="Human required" stroke="#0f766e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category donut */}
        <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-lg">
          <h2 className="text-headline-sm mb-xs">Category Mix</h2>
          <p className="text-body-sm text-on-surface-variant mb-md">Distribution by intent</p>
          {donut.length === 0 ? (
            <p className="text-body-sm text-on-surface-variant py-xl text-center">No classified emails yet.</p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={donut} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                    {donut.map((_, i) => (
                      <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Recent activity (audit) */}
      <div className="mt-lg rounded-xl border border-outline-variant bg-surface-container-lowest overflow-hidden">
        <div className="px-lg py-md border-b border-outline-variant text-label-sm text-on-surface-variant uppercase tracking-wide">
          Recent activity
        </div>
        {audit.length === 0 ? (
          <div className="px-lg py-lg text-center text-body-sm text-on-surface-variant">No activity yet.</div>
        ) : (
          audit.map((a) => (
            <div key={a.id} className="px-lg py-sm border-b border-surface-container-high last:border-0 flex items-center gap-md text-body-sm">
              <span className="inline-block rounded-full bg-surface-container-high text-on-surface-variant px-sm py-unit text-label-sm capitalize w-24 text-center">{a.action}</span>
              <span className="text-on-surface-variant flex-1 truncate font-mono text-code">
                {(a.entity?.type as string) ?? "system"} {a.entity?.category ? `· ${a.entity.category}` : ""}
              </span>
              <span className="text-on-surface-variant">{a.actor_email ?? "system"}</span>
              <span className="text-on-surface-variant">{a.created_at ? new Date(a.created_at).toLocaleString() : ""}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
