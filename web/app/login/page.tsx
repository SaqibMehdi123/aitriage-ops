"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Icon, Logo } from "@/components/ui";

const PAGE_GRADIENT = "linear-gradient(135deg,#1c1917 0%,#292524 45%,#44403c 100%)";
const BTN_GRADIENT = "linear-gradient(135deg,#f59e0b 0%,#d97706 100%)";

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
    <main
      className="min-h-screen flex items-center justify-center px-margin-mobile py-xl relative overflow-hidden"
      style={{ background: PAGE_GRADIENT }}
    >
      {/* decorative glows */}
      <div className="pointer-events-none absolute -top-40 -left-40 w-[28rem] h-[28rem] rounded-full opacity-25"
        style={{ background: "radial-gradient(circle,#f59e0b,transparent 70%)" }} />
      <div className="pointer-events-none absolute -bottom-48 -right-40 w-[32rem] h-[32rem] rounded-full opacity-20"
        style={{ background: "radial-gradient(circle,#fbbf24,transparent 70%)" }} />

      <div className="relative w-full max-w-[26rem]">
        {/* Brand */}
        <div className="flex flex-col items-center text-center mb-lg">
          <Logo size={56} className="mb-md" />
          <h1 className="text-headline-md font-bold tracking-tight text-white">
            AITriage <span className="text-white/70 font-light">Ops</span>
          </h1>
          <p className="text-body-sm text-white/60 mt-unit">AI inbox triage &amp; reply router</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-white/95 backdrop-blur-sm border border-white/40 shadow-2xl p-xl">
          <h2 className="text-headline-sm text-on-surface mb-xs">
            {mode === "signin" ? "Welcome back" : "Create your workspace"}
          </h2>
          <p className="text-body-sm text-on-surface-variant mb-lg">
            {mode === "signin" ? "Sign in to your triage queue." : "Spin up your organisation and inbox."}
          </p>

          <form onSubmit={onSubmit} className="flex flex-col gap-md">
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface-variant">Email</span>
              <div className="relative">
                <Icon name="mail" className="absolute left-sm top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant" />
                <input
                  type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
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
                  type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
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
              type="submit" disabled={loading} style={{ background: BTN_GRADIENT }}
              className="mt-xs rounded-lg text-white py-sm text-label-md font-semibold hover:opacity-95 transition-opacity disabled:opacity-60 shadow-md"
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

        <p className="text-center text-label-sm text-white/50 mt-lg">
          Classify · draft · route — with a human in control.
        </p>
      </div>
    </main>
  );
}
