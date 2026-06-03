"use client";

import { useCallback, useEffect, useState } from "react";
import { createRule, deleteRule, listMembers, listRules, updateRule } from "@/lib/triage";
import type { Member, Rule, RuleCondition } from "@/lib/types";
import { Icon, Spinner } from "@/components/ui";

const FIELDS = ["category", "urgency", "keyword", "from_address"];
const OPS_BY_FIELD: Record<string, string[]> = {
  category: ["eq"],
  urgency: ["eq"],
  keyword: ["contains"],
  from_address: ["contains", "eq"],
};

type Draft = {
  name: string;
  priority: number;
  conditions: RuleCondition[];
  assignee_id: string;
  log_to_crm: boolean;
  is_active: boolean;
};

const emptyDraft = (): Draft => ({
  name: "",
  priority: 100,
  conditions: [{ field: "category", op: "eq", value: "Support" }],
  assignee_id: "",
  log_to_crm: false,
  is_active: true,
});

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const memberName = (id: string | null) =>
    members.find((m) => m.user_id === id)?.full_name ||
    members.find((m) => m.user_id === id)?.email ||
    null;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [r, m] = await Promise.all([listRules(), listMembers().catch(() => [])]);
      setRules(r);
      setMembers(m);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function startNew() {
    setEditingId(null);
    setDraft(emptyDraft());
  }

  function startEdit(r: Rule) {
    setEditingId(r.id);
    setDraft({
      name: r.name ?? "",
      priority: r.priority,
      conditions: r.conditions.all?.length ? r.conditions.all : [{ field: "category", op: "eq", value: "" }],
      assignee_id: r.assignee_id ?? "",
      log_to_crm: Boolean(r.crm_action),
      is_active: r.is_active,
    });
  }

  async function save() {
    if (!draft) return;
    setError(null);
    const payload: Partial<Rule> = {
      name: draft.name || null,
      priority: draft.priority,
      conditions: { all: draft.conditions.filter((c) => c.value !== "") },
      assignee_id: draft.assignee_id || null,
      crm_action: draft.log_to_crm ? { type: "log" } : null,
      is_active: draft.is_active,
    };
    try {
      if (editingId) await updateRule(editingId, payload);
      else await createRule(payload);
      setDraft(null);
      setEditingId(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    }
  }

  async function remove(id: string) {
    await deleteRule(id).catch(() => {});
    setRules((r) => r.filter((x) => x.id !== id));
  }

  function setCond(i: number, patch: Partial<RuleCondition>) {
    setDraft((d) => {
      if (!d) return d;
      const conditions = d.conditions.map((c, idx) => (idx === i ? { ...c, ...patch } : c));
      return { ...d, conditions };
    });
  }

  const Pill = ({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "primary" | "error" }) => {
    const cls =
      tone === "primary" ? "bg-primary-fixed text-on-primary-fixed"
      : tone === "error" ? "bg-error-container text-on-error-container"
      : "bg-surface-container-high text-on-surface";
    return <span className={`rounded px-sm py-unit text-label-md font-medium ${cls}`}>{children}</span>;
  };

  return (
    <div className="p-margin-mobile sm:p-margin-desktop max-w-container-max">
      <header className="mb-lg flex flex-col gap-md sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-display-lg">Routing Rules</h1>
          <p className="text-body-md text-on-surface-variant">Manage automated triaging and assignment workflows.</p>
        </div>
        <button onClick={startNew} className="w-full sm:w-auto justify-center rounded bg-primary text-on-primary px-md py-sm text-label-md font-medium hover:bg-primary-container transition-colors flex items-center gap-xs">
          <Icon name="add" className="text-[18px]" /> Add Rule
        </button>
      </header>

      {error && (
        <div className="mb-md rounded-lg border border-error-container bg-error-container text-on-error-container px-md py-sm text-body-sm">{error}</div>
      )}

      {/* Editor */}
      {draft && (
        <div className="mb-lg rounded-xl border border-primary bg-surface-container-low p-lg">
          <div className="flex flex-wrap items-center gap-md mb-md">
            <input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="Rule name (optional)"
              className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm flex-1 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <label className="text-label-md text-on-surface-variant flex items-center gap-xs">
              Priority
              <input
                type="number"
                value={draft.priority}
                onChange={(e) => setDraft({ ...draft, priority: Number(e.target.value) })}
                className="w-20 rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </label>
          </div>

          {/* Conditions */}
          <div className="flex flex-col gap-sm">
            {draft.conditions.map((c, i) => (
              <div key={i} className="flex flex-wrap items-center gap-sm">
                <Pill>{i === 0 ? "IF" : "AND"}</Pill>
                <select value={c.field} onChange={(e) => setCond(i, { field: e.target.value, op: OPS_BY_FIELD[e.target.value][0] })}
                  className="rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary">
                  {FIELDS.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
                <select value={c.op} onChange={(e) => setCond(i, { op: e.target.value })}
                  className="rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary">
                  {(OPS_BY_FIELD[c.field] ?? ["eq"]).map((o) => <option key={o} value={o}>{o === "eq" ? "=" : o}</option>)}
                </select>
                {c.field === "category" ? (
                  <select value={String(c.value)} onChange={(e) => setCond(i, { value: e.target.value })}
                    className="rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary">
                    {["Support", "Sales", "Billing", "Spam", "Other"].map((v) => <option key={v} value={v}>{v}</option>)}
                  </select>
                ) : c.field === "urgency" ? (
                  <select value={String(c.value)} onChange={(e) => setCond(i, { value: e.target.value })}
                    className="rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary">
                    {["high", "normal", "low"].map((v) => <option key={v} value={v}>{v}</option>)}
                  </select>
                ) : (
                  <input value={String(c.value)} onChange={(e) => setCond(i, { value: e.target.value })}
                    placeholder="value"
                    className="rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary" />
                )}
                {draft.conditions.length > 1 && (
                  <button onClick={() => setDraft({ ...draft, conditions: draft.conditions.filter((_, idx) => idx !== i) })}
                    className="p-unit hover:bg-surface-container rounded text-on-surface-variant"><Icon name="close" className="text-[18px]" /></button>
                )}
              </div>
            ))}
            <button onClick={() => setDraft({ ...draft, conditions: [...draft.conditions, { field: "keyword", op: "contains", value: "" }] })}
              className="self-start text-label-md text-primary hover:underline flex items-center gap-xs">
              <Icon name="add" className="text-[16px]" /> Add condition
            </button>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center gap-sm mt-md pt-md border-t border-outline-variant">
            <Pill tone="primary">THEN</Pill>
            <label className="text-label-md text-on-surface-variant flex items-center gap-xs">
              Assign to
              <select value={draft.assignee_id} onChange={(e) => setDraft({ ...draft, assignee_id: e.target.value })}
                className="rounded border border-outline-variant bg-surface-container-lowest px-sm py-sm text-label-md focus:outline-none focus:ring-2 focus:ring-primary">
                <option value="">— nobody —</option>
                {members.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name || m.email}</option>)}
              </select>
            </label>
            <label className="text-label-md text-on-surface flex items-center gap-xs">
              <input type="checkbox" checked={draft.log_to_crm} onChange={(e) => setDraft({ ...draft, log_to_crm: e.target.checked })} />
              Log to CRM
            </label>
            <label className="text-label-md text-on-surface flex items-center gap-xs">
              <input type="checkbox" checked={draft.is_active} onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })} />
              Active
            </label>
          </div>

          <div className="flex gap-sm mt-md">
            <button onClick={save} className="rounded bg-primary text-on-primary px-md py-sm text-label-md font-medium hover:bg-primary-container transition-colors">Save rule</button>
            <button onClick={() => { setDraft(null); setEditingId(null); }} className="rounded border border-outline-variant px-md py-sm text-label-md hover:bg-surface-container transition-colors">Cancel</button>
          </div>
        </div>
      )}

      {/* Rule list */}
      {loading ? (
        <Spinner label="Loading rules…" />
      ) : rules.length === 0 && !draft ? (
        <div className="rounded-xl border border-dashed border-outline-variant bg-surface-container-low p-xl text-center text-body-sm text-on-surface-variant">
          No rules yet. Click <strong>Add Rule</strong> to route emails to teammates automatically.
        </div>
      ) : (
        <div className="flex flex-col gap-md">
          {rules.map((r) => (
            <div key={r.id} className={`rounded-xl border bg-surface-container-lowest p-lg flex items-center justify-between gap-md ${r.is_active ? "border-outline-variant" : "border-outline-variant opacity-60"}`}>
              <div className="flex flex-wrap items-center gap-sm">
                {r.name && <span className="text-label-md font-semibold text-on-surface mr-sm">{r.name}</span>}
                <Pill>IF</Pill>
                {(r.conditions.all ?? []).map((c, i) => (
                  <span key={i} className="flex items-center gap-sm">
                    {i > 0 && <span className="text-label-sm text-on-surface-variant">AND</span>}
                    <span className="font-mono text-code text-on-surface-variant">{c.field}</span>
                    <span className="text-on-surface-variant">{c.op === "eq" ? "=" : c.op}</span>
                    <Pill tone="primary">{String(c.value)}</Pill>
                  </span>
                ))}
                <Pill tone="primary">THEN</Pill>
                {r.assignee_id && <span className="flex items-center gap-xs text-label-md text-secondary"><Icon name="person_add" className="text-[16px]" /> {memberName(r.assignee_id)}</span>}
                {r.crm_action && <span className="flex items-center gap-xs text-label-md text-on-surface"><Icon name="dataset" className="text-[16px]" /> Log to CRM</span>}
                {!r.assignee_id && !r.crm_action && <span className="text-label-sm text-on-surface-variant">no action</span>}
              </div>
              <div className="flex items-center gap-xs shrink-0">
                <span className="text-label-sm text-on-surface-variant mr-sm">#{r.priority}</span>
                <button onClick={() => startEdit(r)} className="p-xs hover:bg-surface-container rounded text-on-surface-variant"><Icon name="edit" className="text-[20px]" /></button>
                <button onClick={() => remove(r.id)} className="p-xs hover:bg-surface-container rounded text-on-surface-variant"><Icon name="delete" className="text-[20px]" /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
