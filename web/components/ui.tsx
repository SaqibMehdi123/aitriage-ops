// Small presentational primitives shared across screens, styled to the
// "Precision Operations" design system (status chips, urgency dots, avatars).
import type { Urgency } from "@/lib/types";

export function Avatar({ name, className = "" }: { name: string; className?: string }) {
  const initials = (name || "?")
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
  return (
    <div
      className={`shrink-0 rounded-full bg-surface-dim text-on-surface flex items-center justify-center text-label-sm font-semibold ${className}`}
    >
      {initials || "?"}
    </div>
  );
}

const CATEGORY_STYLES: Record<string, string> = {
  Support: "bg-primary-fixed text-on-primary-fixed",
  Sales: "bg-tertiary-fixed text-on-tertiary-fixed",
  Billing: "bg-secondary-fixed text-on-secondary-fixed",
  Spam: "bg-error-container text-on-error-container",
  Other: "bg-surface-container-high text-on-surface-variant",
};

export function CategoryChip({ category }: { category: string | null }) {
  if (!category) return <span className="text-on-surface-variant text-label-sm">—</span>;
  const cls = CATEGORY_STYLES[category] ?? CATEGORY_STYLES.Other;
  return (
    <span className={`inline-block rounded-full px-sm py-unit text-label-sm font-medium ${cls}`}>
      {category}
    </span>
  );
}

const URGENCY_DOT: Record<Urgency, string> = {
  high: "bg-error",
  normal: "bg-tertiary",
  low: "bg-outline",
};

export function UrgencyBadge({ urgency }: { urgency: Urgency | null }) {
  if (!urgency) return <span className="text-on-surface-variant text-label-sm">—</span>;
  return (
    <span className="inline-flex items-center gap-xs text-body-sm capitalize">
      <span className={`w-2 h-2 rounded-full ${URGENCY_DOT[urgency]}`} />
      {urgency}
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  new: "bg-surface-container-high text-on-surface-variant",
  classified: "bg-secondary-fixed text-on-secondary-fixed",
  drafted: "bg-primary-fixed text-on-primary-fixed",
  review: "bg-error-container text-on-error-container",
  sent: "bg-tertiary-fixed text-on-tertiary-fixed",
};

export function StatusChip({ status }: { status: string }) {
  const cls = STATUS_STYLES[status] ?? STATUS_STYLES.new;
  return (
    <span className={`inline-block rounded-full px-sm py-unit text-label-sm font-medium capitalize ${cls}`}>
      {status}
    </span>
  );
}

export function Confidence({ value }: { value: number | null }) {
  if (value == null) return <span className="text-on-surface-variant">—</span>;
  const pct = Math.round(value * 100);
  const low = value < 0.7;
  return <span className={low ? "text-error font-semibold" : "text-on-surface font-medium"}>{pct}%</span>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-sm text-on-surface-variant text-body-sm">
      <span className="ring-spinner w-4 h-4 animate-spin" aria-hidden />
      {label}
    </span>
  );
}

/** Full-screen branded loader for route transitions. */
export function PageLoader() {
  return (
    <div className="h-screen w-full flex flex-col items-center justify-center gap-lg bg-background">
      <div className="relative flex items-center justify-center">
        <span className="ring-spinner w-16 h-16 animate-spin" aria-hidden />
        <span className="triage-mark absolute w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-on-primary">
          <span className="material-symbols-outlined text-[22px]">support_agent</span>
        </span>
      </div>
      <div className="flex items-center gap-xs">
        <span className="triage-dot w-2 h-2 rounded-full bg-primary" style={{ animationDelay: "0ms" }} />
        <span className="triage-dot w-2 h-2 rounded-full bg-primary" style={{ animationDelay: "150ms" }} />
        <span className="triage-dot w-2 h-2 rounded-full bg-primary" style={{ animationDelay: "300ms" }} />
      </div>
      <p className="text-label-sm text-on-surface-variant tracking-wide">Loading AITriage Ops…</p>
    </div>
  );
}

export function Icon({ name, className = "" }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>;
}
