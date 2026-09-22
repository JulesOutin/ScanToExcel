"use client";

import Link from "next/link";
import type { DocumentOut } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Envoyé",
  queued: "En file",
  processing: "En cours",
  needs_review: "À vérifier",
  done: "Terminé",
  failed: "Échec",
};

export function HistoryTable({
  documents,
  selected,
  onToggle,
}: {
  documents: DocumentOut[];
  selected: Set<string>;
  onToggle: (id: string) => void;
}) {
  if (documents.length === 0) {
    return <p className="text-sm text-ink/60">Aucune facture pour l'instant.</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left font-mono text-[11px] text-ink/60 border-b border-rule">
          <th className="pb-2 w-8"></th>
          <th className="pb-2">Fournisseur</th>
          <th className="pb-2">N° facture</th>
          <th className="pb-2">Statut</th>
          <th className="pb-2 text-right">Total</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <tr key={doc.id} className="border-b border-rule/40">
            <td className="py-2">
              <input
                type="checkbox"
                checked={selected.has(doc.id)}
                onChange={() => onToggle(doc.id)}
                disabled={doc.status !== "done" && doc.status !== "needs_review"}
              />
            </td>
            <td className="py-2">
              <Link href={`/documents/${doc.id}`} className="hover:underline underline-offset-2">
                {doc.extracted_data?.supplier.name || doc.original_filename}
              </Link>
            </td>
            <td className="py-2">{doc.extracted_data?.invoice_number || "—"}</td>
            <td className="py-2">{STATUS_LABEL[doc.status] ?? doc.status}</td>
            <td className="py-2 text-right font-mono">
              {doc.extracted_data ? `${doc.extracted_data.total.toFixed(2)} ${doc.extracted_data.currency}` : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
