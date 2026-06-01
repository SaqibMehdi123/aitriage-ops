"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

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
    <main className="min-h-screen flex items-center justify-center bg-background px-margin-mobile">
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="flex items-center gap-sm mb-xl justify-center">
          <div className="w-10 h-10 rounded bg-primary flex items-center justify-center text-on-primary">
            <span className="material-symbols-outlined text-[24px]">support_agent</span>
          </div>
          <div>
            <h1 className="text-headline-sm font-bold text-primary">AITriage Ops</h1>
            <p className="text-label-sm text-on-surface-variant">High-Velocity Support</p>
          </div>
        </div>

        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-xl shadow-elevated">
          <h2 className="text-headline-md mb-xs">
            {mode === "signin" ? "Sign in" : "Create your workspace"}
          </h2>
          <p className="text-body-sm text-on-surface-variant mb-lg">
            {mode === "signin"
              ? "Welcome back. Sign in to your triage queue."
              : "Sign up to spin up your organisation and inbox."}
          </p>

          <form onSubmit={onSubmit} className="flex flex-col gap-md">
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface-variant">Email</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="you@company.com"
              />
            </label>
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface-variant">Password</span>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="••••••••"
              />
            </label>

            {error && (
              <p className="text-label-md text-on-error-container bg-error-container rounded px-md py-sm">
                {error}
              </p>
            )}
            {info && (
              <p className="text-label-md text-on-secondary-fixed bg-secondary-fixed rounded px-md py-sm">
                {info}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-xs rounded bg-primary text-on-primary py-sm text-label-md font-medium hover:bg-primary-container transition-colors disabled:opacity-60"
            >
              {loading ? "Please wait…" : mode === "signin" ? "Sign in" : "Sign up"}
            </button>
          </form>

          <p className="text-body-sm text-on-surface-variant mt-lg text-center">
            {mode === "signin" ? "No account yet?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() => {
                setMode(mode === "signin" ? "signup" : "signin");
                setError(null);
                setInfo(null);
              }}
              className="text-primary font-medium hover:underline"
            >
              {mode === "signin" ? "Create one" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </main>
  );
}
