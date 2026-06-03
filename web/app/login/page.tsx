"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Icon, Logo } from "@/components/ui";
import AuthSocial from "@/components/AuthSocial";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();
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
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      router.push("/queue");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function forgotPassword() {
    if (!email) {
      setError("Enter your email above first, then click “Forgot password?”.");
      return;
    }
    setError(null);
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/login`,
    });
    if (error) setError(error.message);
    else setInfo("Password reset link sent — check your email.");
  }

  return (
    <main className="min-h-screen flex text-on-surface">
      <div className="fixed top-0 left-0 w-full h-1 bg-primary z-50" />

      {/* Left hero */}
      <section className="hidden md:flex md:w-1/2 lg:w-3/5 bg-surface-container-low dot-grid flex-col justify-center items-start p-xl lg:p-[64px] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-fixed/40 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-lg">
          <h1 className="text-display-lg lg:text-[40px] lg:leading-[48px] font-semibold tracking-tight mb-lg">
            Automate the inbox.<br />
            <span className="text-primary">Empower the team.</span>
          </h1>
          <p className="text-body-md text-on-surface-variant lg:text-body-md">
            Precision engineering for modern operations. AITriage Ops streamlines your
            data flow with intelligent, context-aware automation designed for
            high-performance environments.
          </p>

          {/* Decorative mini-dashboard */}
          <div className="mt-xl rounded-xl border border-outline-variant bg-surface-container-lowest/70 backdrop-blur-sm p-lg shadow-elevated">
            <div className="flex items-center justify-between mb-md">
              <span className="text-label-sm text-on-surface-variant uppercase tracking-wide">Processing volume</span>
              <span className="text-label-sm text-primary font-semibold">+18%</span>
            </div>
            <svg viewBox="0 0 300 90" className="w-full h-24">
              <polyline fill="none" stroke="#d97706" strokeWidth="2.5"
                points="0,70 40,60 80,64 120,40 160,46 200,28 240,32 300,16" />
              <polyline fill="none" stroke="#57534e" strokeWidth="2" strokeOpacity="0.5"
                points="0,80 40,76 80,78 120,68 160,72 200,64 240,66 300,58" />
            </svg>
            <div className="flex gap-sm mt-md">
              {["Support", "Sales", "Billing"].map((c, i) => (
                <span key={c} className={`text-label-sm px-sm py-unit rounded-full ${["bg-primary-fixed text-on-primary-fixed", "bg-tertiary-fixed text-on-tertiary-fixed", "bg-secondary-fixed text-on-secondary-fixed"][i]}`}>{c}</span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Right form */}
      <section className="w-full md:w-1/2 lg:w-2/5 flex items-center justify-center p-md md:p-xl bg-surface relative">
        <div className="w-full max-w-[440px] bg-surface-container-lowest rounded-xl border border-outline-variant/40 shadow-elevated p-xl">
          <div className="text-center mb-xl">
            <div className="flex items-center justify-center gap-sm mb-md">
              <Logo size={36} />
              <span className="text-headline-sm font-bold text-on-surface">AITriage Ops</span>
            </div>
            <h2 className="text-headline-md mb-xs">Welcome back</h2>
            <p className="text-body-sm text-on-surface-variant">Sign in to your operational dashboard.</p>
          </div>

          <AuthSocial providers={["google", "azure"]} />

          <div className="flex items-center my-lg">
            <div className="flex-grow h-px bg-outline-variant/60" />
            <span className="px-md text-label-sm text-on-surface-variant uppercase tracking-wider">or sign in with email</span>
            <div className="flex-grow h-px bg-outline-variant/60" />
          </div>

          <form onSubmit={onSubmit} className="flex flex-col gap-md">
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface">Work Email</span>
              <div className="relative">
                <Icon name="mail" className="absolute left-sm top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
                <input
                  type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-md py-sm rounded-lg border border-outline-variant bg-surface-container-lowest text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="name@company.com"
                />
              </div>
            </label>
            <label className="flex flex-col gap-xs">
              <div className="flex justify-between items-center">
                <span className="text-label-md text-on-surface">Password</span>
                <button type="button" onClick={forgotPassword} className="text-label-sm text-primary hover:underline">Forgot password?</button>
              </div>
              <div className="relative">
                <Icon name="lock" className="absolute left-sm top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
                <input
                  type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-md py-sm rounded-lg border border-outline-variant bg-surface-container-lowest text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>
            </label>

            <label className="flex items-center gap-sm text-body-sm text-on-surface-variant cursor-pointer select-none">
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded-sm accent-[#b45309]" />
              Remember this device
            </label>

            {error && <p className="text-label-md text-on-error-container bg-error-container rounded-lg px-md py-sm">{error}</p>}
            {info && <p className="text-label-md text-on-tertiary-fixed bg-tertiary-fixed rounded-lg px-md py-sm">{info}</p>}

            <button
              type="submit" disabled={loading}
              className="w-full bg-primary hover:bg-primary-container text-on-primary text-label-md font-semibold py-sm rounded-lg transition-colors flex justify-center items-center gap-sm disabled:opacity-60"
            >
              {loading ? "Authenticating…" : "Sign In"}
              {!loading && <Icon name="arrow_forward" className="text-[18px]" />}
            </button>
          </form>

          <p className="mt-xl text-center text-body-sm text-on-surface-variant">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-primary font-semibold hover:underline">Sign up</Link>
          </p>
        </div>

        <div className="absolute bottom-lg left-0 w-full text-center hidden sm:block">
          <p className="text-label-sm text-on-surface-variant/70">© 2024 AITriage Ops. Precision Engineering.</p>
        </div>
      </section>
    </main>
  );
}
