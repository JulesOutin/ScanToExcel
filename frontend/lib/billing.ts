import { getAccessToken } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export interface SubscriptionOut {
  plan: "free" | "personal" | "pro";
  status: string;
}

async function authHeaders(): Promise<HeadersInit> {
  const token = await getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getSubscription(): Promise<SubscriptionOut> {
  const res = await fetch(`${API_URL}/billing/subscription`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Échec du chargement de l'abonnement (${res.status})`);
  return res.json();
}

export async function startCheckout(plan: "personal" | "pro"): Promise<void> {
  const res = await fetch(`${API_URL}/billing/checkout`, {
    method: "POST",
    headers: { ...(await authHeaders()), "Content-Type": "application/json" },
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) throw new Error(`Échec de la création du paiement (${res.status})`);
  const { url } = await res.json();
  window.location.href = url;
}

export async function openBillingPortal(): Promise<void> {
  const res = await fetch(`${API_URL}/billing/portal`, {
    method: "POST",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Échec de l'ouverture du portail (${res.status})`);
  const { url } = await res.json();
  window.location.href = url;
}
