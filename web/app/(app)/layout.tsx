import { redirect } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { createClient } from "@/lib/supabase/server";

// Authenticated shell: fixed sidebar + scrollable main content (256px sidebar
// per the design's fixed-grid desktop layout).
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      <Sidebar />
      <main className="flex-1 ml-64 h-full overflow-y-auto">{children}</main>
    </div>
  );
}
