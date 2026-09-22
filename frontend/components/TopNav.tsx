"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabaseBrowserClient } from "@/lib/supabase";

export function TopNav() {
  const router = useRouter();

  const signOut = async () => {
    await supabaseBrowserClient().auth.signOut();
    router.push("/");
    router.refresh();
  };

  return (
    <nav className="max-w-3xl mx-auto px-5 pt-5 flex justify-between items-center text-sm">
      <Link href="/app" className="font-mono text-xs text-ink/60">SCANTOEXCEL</Link>
      <div className="flex gap-4 items-center">
        <Link href="/facturation" className="text-ink/70 hover:text-ink">Facturation</Link>
        <button onClick={signOut} className="text-ink/70 hover:text-ink">Se déconnecter</button>
      </div>
    </nav>
  );
}
