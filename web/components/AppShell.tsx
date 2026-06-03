"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Logo } from "@/components/ui";

/**
 * Responsive authenticated shell. On desktop (lg+) the sidebar is a fixed 256px
 * rail and content sits to its right. On mobile/tablet the sidebar becomes an
 * off-canvas drawer toggled by the hamburger in the top bar, with a tap-to-close
 * backdrop.
 */
export default function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      <Sidebar open={open} onClose={() => setOpen(false)} />

      {/* Backdrop — only while the drawer is open on mobile/tablet. */}
      {open && (
        <button
          aria-label="Close menu"
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
        />
      )}

      <div className="flex-1 flex flex-col h-full overflow-hidden lg:ml-64">
        {/* Mobile/tablet top bar with menu toggle. */}
        <div className="lg:hidden flex items-center gap-sm border-b border-outline-variant bg-surface px-md py-sm shrink-0">
          <button
            aria-label="Open menu"
            onClick={() => setOpen(true)}
            className="flex items-center justify-center rounded p-xs text-on-surface-variant hover:bg-surface-container transition-colors"
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
          <div className="flex items-center gap-sm">
            <Logo size={28} />
            <span className="text-title-lg font-bold text-primary">AITriage Ops</span>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
