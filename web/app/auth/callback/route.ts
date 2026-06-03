import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// OAuth (Google/Microsoft/GitHub) redirect lands here with a `code`; we exchange
// it for a session (cookies set via the server client) and continue into the app.
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/queue";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) return NextResponse.redirect(`${origin}${next}`);
  }
  return NextResponse.redirect(`${origin}/login?error=oauth_failed`);
}
