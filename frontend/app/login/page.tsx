"use client";

import { useState } from "react";
import { supabaseBrowserClient } from "@/lib/supabase";

type Mode = "magic-link" | "password";

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>("magic-link");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const supabase = supabaseBrowserClient();

  const sendMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("sending");
    setError(null);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      setError(error.message);
      setStatus("error");
    } else {
      setStatus("sent");
    }
  };

  const signInWithPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("sending");
    setError(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setError(error.message);
      setStatus("error");
    } else {
      window.location.href = "/";
    }
  };

  return (
    <main className="max-w-sm mx-auto px-5 py-20">
      <p className="font-mono text-xs text-ink/60 mb-1.5">SCANTOEXCEL</p>
      <h1 className="font-display font-bold text-3xl mb-6">Se connecter</h1>

      {mode === "magic-link" ? (
        <form onSubmit={sendMagicLink} className="space-y-3">
          <div>
            <label className="block text-[11px] font-mono text-ink/60 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-rule bg-paper-raised px-3 py-2.5 text-sm focus:outline-none focus:border-accent"
              placeholder="toi@exemple.fr"
            />
          </div>
          <button
            type="submit"
            disabled={status === "sending"}
            className="w-full bg-accent text-white rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-50"
          >
            {status === "sending" ? "Envoi…" : "Recevoir un lien de connexion"}
          </button>
          {status === "sent" && (
            <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
              Lien envoyé — vérifie ta boîte mail.
            </p>
          )}
        </form>
      ) : (
        <form onSubmit={signInWithPassword} className="space-y-3">
          <div>
            <label className="block text-[11px] font-mono text-ink/60 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-rule bg-paper-raised px-3 py-2.5 text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="block text-[11px] font-mono text-ink/60 mb-1">Mot de passe</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-rule bg-paper-raised px-3 py-2.5 text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <button
            type="submit"
            disabled={status === "sending"}
            className="w-full bg-accent text-white rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-50"
          >
            {status === "sending" ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      )}

      {error && <p className="mt-3 text-sm text-orange-800 bg-orange-100 rounded-lg px-3 py-2">{error}</p>}

      <button
        onClick={() => setMode(mode === "magic-link" ? "password" : "magic-link")}
        className="mt-4 text-accent underline underline-offset-2 text-sm"
      >
        {mode === "magic-link" ? "Se connecter avec un mot de passe à la place" : "Recevoir un lien par email à la place"}
      </button>
    </main>
  );
}
