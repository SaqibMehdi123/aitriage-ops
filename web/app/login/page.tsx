"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Icon, Logo } from "@/components/ui";

const FEATURES = [
  { icon: "bolt", title: "Instant triage", desc: "Every email classified by intent, urgency, and confidence." },
  { icon: "auto_awesome", title: "Grounded AI replies", desc: "Drafts written from your own knowledge base, with citations." },
  { icon: "alt_route", title: "Smart routing", desc: "Rules send each message to the right person, automatically." },
];

const PANEL_GRADIENT = "linear-gradient(150deg,#2f2ebe 0%,#3b309e 45%,#534ab7 100%)";
const BTN_GRADIENT = "linear-gradient(135deg,#6d63e6 0%,#3b309e 100%)";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setLoading(true);
    try {
      if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.push("/queue");
        router.refresh();
      } else {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (data.session) {
          router.push("/queue");
          router.refresh();
        } else {
          setInfo("Account created. Check your email to confirm, then sign in.");
          setMode("signin");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen grid lg:grid-cols-2 bg-surface-container-low">
      {/* Brand panel */}
      <aside
        className="relative hidden lg:flex flex-col justify-between p-xl text-white overflow-hidden"
        style={{ background: PANEL_GRADIENT }}
      >
        {/* soft decorative glow */}
        <div className="pointer-events-none absolute -top-24 -right-24 w-96 h-96 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle,#c5c0ff,transparent 70%)" }} />
        <div className="pointer-events-none absolute -bottom-32 -left-16 w-96 h-96 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle,#6063ee,transparent 70%)" }} />

        <div className="relative flex items-center gap-sm">
          <Logo size={40} />
          <div>
            <h1 className="text-headline-sm font-bold leading-tight">AITriage Ops</h1>
            <p className="text-label-sm text-white/70">High-Velocity Support</p>
          </div>
        </div>

        <div className="relative max-w-md">
          <h2 className="text-display-lg font-semibold leading-tight mb-md">
            Triage your inbox at the speed of AI.
          </h2>
          <p className="text-body-md text-white/80 mb-xl">
            Classify, draft, and route every incoming email — with a human in
            control of what gets sent.
          </p>
          <ul className="flex flex-col gap-lg">
            {FEATURES.map((f) => (
              <li key={f.title} className="flex items-start gap-md">
                <span className="shrink-0 w-10 h-10 rounded-lg bg-white/15 backdrop-blur flex items-center justify-center">
                  <Icon name={f.icon} className="text-[22px]" />
                </span>
                <div>
                  <p className="text-title-lg font-medium">{f.title}</p>
                  <p className="text-body-sm text-white/75">{f.desc}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-label-sm text-white/60">
          Cut manual triage by ~70% · respond in seconds, not minutes.
        </p>
      </aside>

      {/* Form panel */}
      <section className="flex items-center justify-center p-margin-mobile sm:p-xl">
        <div className="w-full max-w-md">
          {/* compact brand for mobile */}
          <div className="flex lg:hidden items-center gap-sm mb-xl justify-center">
            <Logo size={36} />
            <h1 className="text-headline-sm font-bold text-primary">AITriage Ops</h1>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-xl shadow-elevated">
            <h2 className="text-headline-md mb-xs">
              {mode === "signin" ? "Welcome back" : "Create your workspace"}
            </h2>
            <p className="text-body-sm text-on-surface-variant mb-lg">
              {mode === "signin"
                ? "Sign in to your triage queue."
                : "Spin up your organisation and connected inbox."}
            </p>

            <form onSubmit={onSubmit} className="flex flex-col gap-md">
              <label className="flex flex-col gap-xs">
                <span className="text-label-md text-on-surface-variant">Email</span>
                <div className="relative">
                  <Icon name="mail" className="absolute left-sm top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest pl-10 pr-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="you@company.com"
                  />
                </div>
              </label>
              <label className="flex flex-col gap-xs">
                <span className="text-label-md text-on-surface-variant">Password</span>
                <div className="relative">
                  <Icon name="lock" className="absolute left-sm top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest pl-10 pr-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="••••••••"
                  />
                </div>
              </label>

              {error && (
                <p className="text-label-md text-on-error-container bg-error-container rounded-lg px-md py-sm">{error}</p>
              )}
              {info && (
                <p className="text-label-md text-on-secondary-fixed bg-secondary-fixed rounded-lg px-md py-sm">{info}</p>
              )}

              <button
                type="submit"
                disabled={loading}
                style={{ background: BTN_GRADIENT }}
                className="mt-xs rounded-lg text-white py-sm text-label-md font-semibold hover:opacity-95 transition-opacity disabled:opacity-60 shadow-sm"
              >
                {loading ? "Please wait…" : mode === "signin" ? "Sign in" : "Create workspace"}
              </button>
            </form>

            <p className="text-body-sm text-on-surface-variant mt-lg text-center">
              {mode === "signin" ? "New here?" : "Already have an account?"}{" "}
              <button
                type="button"
                onClick={() => { setMode(mode === "signin" ? "signup" : "signin"); setError(null); setInfo(null); }}
                className="text-primary font-semibold hover:underline"
              >
                {mode === "signin" ? "Create an account" : "Sign in"}
              </button>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
