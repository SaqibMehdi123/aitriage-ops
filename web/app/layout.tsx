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
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-on-surface antialiased">
        {children}
      </body>
    </html>
  );
}
