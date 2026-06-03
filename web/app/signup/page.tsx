"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Icon, Logo } from "@/components/ui";
import AuthSocial from "@/components/AuthSocial";

const VALUE_PROPS = [
  { icon: "smart_toy", title: "AI-Powered Triage", desc: "Automatically categorize and prioritize incoming tickets by intent, urgency, and confidence." },
  { icon: "alt_route", title: "Smart Routing", desc: "Direct each message to the right teammate based on your rules and workload." },
  { icon: "insights", title: "Actionable Analytics", desc: "Deep-dive into volume, response time, and quality with real-time metrics." },
];

export default function SignupPage() {
  const router = useRouter();
  const supabase = createClient();
  const [fullName, setFullName] = useState("");
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
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { full_name: fullName } },
      });
      if (error) throw error;
      if (data.session) {
        router.push("/queue");
        router.refresh();
      } else {
        setInfo("Account created. Check your email to confirm, then sign in.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex text-on-surface">
      <div className="fixed top-0 left-0 w-full h-1 bg-primary z-50" />

      {/* Left value props */}
      <section className="hidden lg:flex w-1/2 flex-col justify-between p-xl lg:p-[64px] bg-surface-container-low dot-grid border-r border-outline-variant/30 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-fixed/40 to-transparent pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center gap-sm mb-xl">
            <Logo size={36} />
            <span className="text-headline-sm font-bold text-on-surface">AITriage Ops</span>
          </div>
          <h1 className="text-display-lg lg:text-[40px] lg:leading-[48px] font-semibold tracking-tight mb-lg max-w-md">
            Engineered for High-Performance Operations.
          </h1>
          <p className="text-body-md text-on-surface-variant mb-xl max-w-md">
            Join the platform that transforms a chaotic inbox into precise, actionable
            workflows — with a human in control of every reply.
          </p>
          <div className="flex flex-col gap-lg max-w-md">
            {VALUE_PROPS.map((v) => (
              <div key={v.title} className="flex gap-md">
                <div className="shrink-0 w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant/50 flex items-center justify-center">
                  <Icon name={v.icon} className="text-primary text-[22px]" />
                </div>
                <div>
                  <h3 className="text-title-lg font-medium text-on-surface">{v.title}</h3>
                  <p className="text-body-sm text-on-surface-variant mt-unit">{v.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="relative z-10 mt-xl pt-lg flex justify-between items-center border-t border-outline-variant/50 text-on-surface-variant">
          <span className="text-label-sm">© 2024 AITriage Ops</span>
          <div className="flex gap-md">
            <span className="text-label-sm">Privacy</span>
            <span className="text-label-sm">Terms</span>
          </div>
        </div>
      </section>

      {/* Right form */}
      <section className="flex-1 flex flex-col justify-center items-center p-md md:p-xl bg-surface">
        <div className="lg:hidden flex items-center gap-sm mb-xl">
          <Logo size={36} />
          <span className="text-headline-sm font-bold text-on-surface">AITriage Ops</span>
        </div>

        <div className="w-full max-w-[440px] bg-surface-container-lowest rounded-xl border border-outline-variant/40 shadow-elevated p-xl">
          <div className="mb-xl text-center">
            <h2 className="text-headline-md">Get started for free</h2>
            <p className="text-body-sm text-on-surface-variant mt-xs">Deploy precision operations in minutes.</p>
          </div>

          <AuthSocial providers={["google"]} />

          <div className="flex items-center my-lg">
            <div className="h-px bg-outline-variant/60 flex-1" />
            <span className="px-md text-label-sm text-on-surface-variant uppercase tracking-wider">or sign up with email</span>
            <div className="h-px bg-outline-variant/60 flex-1" />
          </div>

          <form onSubmit={onSubmit} className="flex flex-col gap-md">
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface">Full Name</span>
              <input
                type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)}
                className="w-full px-md py-sm rounded-lg border border-outline-variant bg-surface-container-lowest text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="Jane Doe"
              />
            </label>
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface">Work Email</span>
              <input
                type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full px-md py-sm rounded-lg border border-outline-variant bg-surface-container-lowest text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="jane@company.com"
              />
            </label>
            <label className="flex flex-col gap-xs">
              <span className="text-label-md text-on-surface">Password</span>
              <input
                type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full px-md py-sm rounded-lg border border-outline-variant bg-surface-container-lowest text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="••••••••"
              />
            </label>

            {error && <p className="text-label-md text-on-error-container bg-error-container rounded-lg px-md py-sm">{error}</p>}
            {info && <p className="text-label-md text-on-tertiary-fixed bg-tertiary-fixed rounded-lg px-md py-sm">{info}</p>}

            <button
              type="submit" disabled={loading}
              className="w-full bg-primary hover:bg-primary-container text-on-primary text-label-md font-semibold py-sm rounded-lg transition-colors disabled:opacity-60"
            >
              {loading ? "Creating account…" : "Create Account"}
            </button>
          </form>

          <p className="text-label-sm text-on-surface-variant mt-md text-center">
            By signing up, you agree to our Terms of Service and Privacy Policy.
          </p>
          <p className="mt-md text-center text-body-sm text-on-surface-variant">
            Already have an account?{" "}
            <Link href="/login" className="text-primary font-semibold hover:underline">Log in</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
