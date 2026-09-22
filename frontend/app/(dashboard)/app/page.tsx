"use client";

import { useCallback, useEffect, useState } from "react";
import { UploadZone } from "@/components/UploadZone";
import { ExtractionSheet } from "@/components/ExtractionSheet";
import { HistoryTable } from "@/components/HistoryTable";
import { uploadDocument, listDocuments, updateDocument, exportDocuments, getDocument, type DocumentOut, type ExtractedInvoice } from "@/lib/api";

const POLL_MS = 2000;

export default function HomePage() {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [active, setActive] = useState<DocumentOut | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
    } catch (e) {
      // silencieux : l'utilisateur n'est peut-être pas encore authentifié
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Polling léger tant qu'un document est en cours de traitement (le traitement est asynchrone côté worker)
  useEffect(() => {
    const hasPending = documents.some((d) => d.status === "queued" || d.status === "processing");
    if (!hasPending) return;
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, [documents, refresh]);

  const handleFile = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const doc = await uploadDocument(file);
      setDocuments((prev) => [doc, ...prev]);
      // on suit ce document jusqu'à ce qu'il soit prêt à être corrigé
      const poll = setInterval(async () => {
        const updated = await getDocument(doc.id);
        setDocuments((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
        if (updated.status === "done" || updated.status === "needs_review") {
          clearInterval(poll);
          setActive(updated);
        } else if (updated.status === "failed") {
          clearInterval(poll);
          setError(updated.error_message ?? "L'extraction a échoué.");
        }
      }, POLL_MS);
    } catch (e: any) {
      setError(e.message ?? "Échec de l'envoi.");
    } finally {
      setBusy(false);
    }
  };

  const saveActive = async (next: ExtractedInvoice) => {
    if (!active) return;
    setActive({ ...active, extracted_data: next });
    await updateDocument(active.id, next);
    refresh();
  };

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const doExport = async (format: "xlsx" | "csv" | "fec") => {
    const blob = await exportDocuments([...selected], format);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download =
      format === "xlsx" ? "scantoexcel-export.xlsx"
      : format === "csv" ? "scantoexcel-factures.csv"
      : "scantoexcel-export-fec.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="max-w-3xl mx-auto px-5 py-10 pb-20">
      <header className="mb-8">
        <p className="font-mono text-xs text-ink/60 mb-1.5">SCANTOEXCEL</p>
        <h1 className="font-display font-bold text-4xl leading-tight mb-2">
          Une facture entre,<br /><em className="italic font-medium text-accent">un tableur</em> sort.
        </h1>
        <p className="max-w-[46ch] text-ink/70">
          Dépose une facture, vérifie les données extraites, exporte le lot en Excel ou CSV.
        </p>
      </header>

      <section className="bg-paper-raised border border-rule/60 rounded-2xl p-6 mb-6">
        <h2 className="font-display text-lg mb-1">1. Déposer un document</h2>
        <p className="text-sm text-ink/60 mb-4">Un fichier à la fois — PDF (1ère page) ou image.</p>
        <UploadZone onFile={handleFile} disabled={busy} />
        {error && <p className="mt-3 text-sm text-orange-800 bg-orange-100 rounded-lg px-3 py-2">{error}</p>}
      </section>

      {active?.extracted_data && (
        <div className="mb-6">
          <ExtractionSheet value={active.extracted_data} onChange={saveActive} />
        </div>
      )}

      <section className="bg-paper-raised border border-rule/60 rounded-2xl p-6">
        <h2 className="font-display text-lg mb-1">2. Historique</h2>
        <p className="text-sm text-ink/60 mb-4">Sélectionne les factures à exporter.</p>
        <HistoryTable documents={documents} selected={selected} onToggle={toggleSelected} />
        <div className="flex gap-3 mt-4">
          <button
            disabled={selected.size === 0}
            onClick={() => doExport("xlsx")}
            className="bg-accent text-white rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-40"
          >
            Exporter en Excel (.xlsx)
          </button>
          <button
            disabled={selected.size === 0}
            onClick={() => doExport("csv")}
            className="border border-rule rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-40"
          >
            Exporter en CSV
          </button>
          <button
            disabled={selected.size === 0}
            onClick={() => doExport("fec")}
            className="border border-rule rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-40"
            title="Format FEC — importable dans Pennylane, Sage, QuickBooks, Indy…"
          >
            Export comptable (FEC)
          </button>
        </div>
      </section>
    </main>
  );
}
