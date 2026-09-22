/**
 * Client HTTP minimal vers l'API FastAPI. Attache le JWT Supabase courant
 * à chaque appel authentifié.
 */
import { getAccessToken } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type DocumentStatus =
  | "uploaded" | "queued" | "processing" | "needs_review" | "done" | "failed";

export interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  total: number;
}

export interface ExtractedInvoice {
  document_type: string;
  supplier: { name: string; registration_number: string; address: string };
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  currency: string;
  subtotal: number;
  tax: number;
  total: number;
  items: LineItem[];
  confidence: number;
}

export interface DocumentOut {
  id: string;
  original_filename: string;
  status: DocumentStatus;
  confidence: number | null;
  extracted_data: ExtractedInvoice | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

async function authHeaders(): Promise<HeadersInit> {
  const token = await getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function uploadDocument(file: File): Promise<DocumentOut> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/documents`, {
    method: "POST",
    headers: await authHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Échec de l'envoi (${res.status})`);
  }
  return res.json();
}

export async function listDocuments(): Promise<DocumentOut[]> {
  const res = await fetch(`${API_URL}/documents`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Échec du chargement (${res.status})`);
  return res.json();
}

export async function getDocument(id: string): Promise<DocumentOut> {
  const res = await fetch(`${API_URL}/documents/${id}`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Document introuvable (${res.status})`);
  return res.json();
}

export async function updateDocument(id: string, data: ExtractedInvoice): Promise<DocumentOut> {
  const res = await fetch(`${API_URL}/documents/${id}`, {
    method: "PATCH",
    headers: { ...(await authHeaders()), "Content-Type": "application/json" },
    body: JSON.stringify({ extracted_data: data }),
  });
  if (!res.ok) throw new Error(`Échec de la mise à jour (${res.status})`);
  return res.json();
}

export async function exportDocuments(ids: string[], format: "xlsx" | "csv"): Promise<Blob> {
  const res = await fetch(`${API_URL}/documents/export`, {
    method: "POST",
    headers: { ...(await authHeaders()), "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: ids, format }),
  });
  if (!res.ok) throw new Error(`Échec de l'export (${res.status})`);
  return res.blob();
}
