"use client";

import { useEffect, useState } from "react";
import { getSubscription, startCheckout, openBillingPortal, type SubscriptionOut } from "@/lib/billing";

const PLAN_LABEL: Record<string, string> = { free: "Gratuit", personal: "Personnel", pro: "Professionnel" };

export default function BillingPage() {
  const [sub, setSub] = useState<SubscriptionOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getSubscription().then(setSub).catch((e) => setError(e.message));
  }, []);

  const upgrade = async (plan: "personal" | "pro") => {
    setBusy(true);
    setError(null);
    try {
      await startCheckout(plan);
    } catch (e: any) {
      setError(e.message);
      setBusy(false);
    }
  };

  const manage = async () => {
    setBusy(true);
    setError(null);
    try {
      await openBillingPortal();
    } catch (e: any) {
      setError(e.message);
      setBusy(false);
    }
  };

  return (
    <main className="max-w-3xl mx-auto px-5 py-10">
      <h1 className="font-display font-bold text-3xl mb-2">Facturation</h1>
      <p className="text-ink/70 mb-8">
        Plan actuel : <strong>{sub ? PLAN_LABEL[sub.plan] : "…"}</strong>
        {sub && sub.plan === "free" && " — 20 pages / mois"}
      </p>

      {error && <p className="mb-4 text-sm text-orange-800 bg-orange-100 rounded-lg px-3 py-2">{error}</p>}

      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-paper-raised border border-rule/60 rounded-2xl p-6">
          <h2 className="font-display text-lg mb-1">Personnel</h2>
          <p className="text-sm text-ink/60 mb-4">Pour un usage indépendant régulier.</p>
          <button
            disabled={busy || sub?.plan === "personal"}
            onClick={() => upgrade("personal")}
            className="bg-accent text-white rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-40"
          >
            {sub?.plan === "personal" ? "Plan actuel" : "Passer à Personnel"}
          </button>
        </div>
        <div className="bg-paper-raised border border-rule/60 rounded-2xl p-6">
          <h2 className="font-display text-lg mb-1">Professionnel</h2>
          <p className="text-sm text-ink/60 mb-4">Pour cabinets comptables et volumes élevés.</p>
          <button
            disabled={busy || sub?.plan === "pro"}
            onClick={() => upgrade("pro")}
            className="bg-accent text-white rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-40"
          >
            {sub?.plan === "pro" ? "Plan actuel" : "Passer à Professionnel"}
          </button>
        </div>
      </div>

      {sub && sub.plan !== "free" && (
        <button onClick={manage} className="mt-6 text-accent underline underline-offset-2 text-sm">
          Gérer mon abonnement (portail Stripe)
        </button>
      )}
    </main>
  );
}
