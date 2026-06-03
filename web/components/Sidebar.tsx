"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Logo } from "@/components/ui";

type NavItem = { href: string; label: string; icon: string };

const NAV: NavItem[] = [
  { href: "/queue", label: "Queue", icon: "inbox" },
  { href: "/rules", label: "Rules", icon: "rule" },
  { href: "/knowledge", label: "Knowledge Base", icon: "auto_stories" },
  { href: "/analytics", label: "Analytics", icon: "monitoring" },
  { href: "/settings", label: "Settings", icon: "settings" },
];

export default function Sidebar({
  open = false,
  onClose,
}: {
  open?: boolean;
  onClose?: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <nav
      className={[
        // Off-canvas drawer on mobile/tablet; fixed rail on desktop (lg+).
        "fixed left-0 top-0 h-screen w-64 border-r border-outline-variant bg-surface flex flex-col py-md shrink-0 z-30",
        "transition-transform duration-200 ease-out lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      ].join(" ")}
    >
      {/* Brand */}
      <div className="px-md mb-xl flex items-center gap-sm">
        <Logo size={36} />
        <div>
          <h1 className="text-headline-sm font-bold text-primary leading-tight">AITriage Ops</h1>
          <p className="text-label-sm text-on-surface-variant font-normal">High-Velocity Support</p>
        </div>
      </div>

      {/* Primary nav */}
      <div className="flex-1 flex flex-col gap-xs px-sm">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={[
                "flex items-center gap-md px-md py-sm rounded-r-full transition-colors",
                active
                  ? "border-l-2 border-primary bg-surface-container-low text-primary font-bold"
                  : "text-on-surface-variant hover:bg-surface-container",
              ].join(" ")}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="text-label-md">{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-auto border-t border-outline-variant pt-sm px-sm flex flex-col gap-xs">
        <Link
          href="/support"
          onClick={onClose}
          className="flex items-center gap-md px-md py-sm rounded-r-full text-on-surface-variant hover:bg-surface-container transition-colors"
        >
          <span className="material-symbols-outlined">contact_support</span>
          <span className="text-label-md">Support</span>
        </Link>
        <button
          onClick={signOut}
          className="flex items-center gap-md px-md py-sm rounded-r-full text-on-surface-variant hover:bg-surface-container transition-colors text-left"
        >
          <span className="material-symbols-outlined">logout</span>
          <span className="text-label-md">Sign Out</span>
        </button>
      </div>
    </nav>
  );
}
