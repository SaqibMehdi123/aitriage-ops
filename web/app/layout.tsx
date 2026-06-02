import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AITriage Ops — Inbox Triage + Reply Router",
  description: "AI-assisted inbox triage with human-in-the-loop review.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // suppressHydrationWarning: some browser extensions (e.g. Heurio, Grammarly)
  // inject attributes/elements into <html>/<body> before React hydrates, which
  // would otherwise trigger a hydration mismatch. This only suppresses warnings
  // for these top-level nodes, not real app markup.
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="min-h-screen bg-background text-on-surface antialiased"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
