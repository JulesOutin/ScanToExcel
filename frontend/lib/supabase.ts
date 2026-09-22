/** Client Supabase (navigateur) — utilisé pour l'auth. */
import { createBrowserClient } from "@supabase/ssr";

export function supabaseBrowserClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

export async function getAccessToken(): Promise<string | null> {
  const supabase = supabaseBrowserClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
