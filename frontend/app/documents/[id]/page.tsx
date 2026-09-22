"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ExtractionSheet } from "@/components/ExtractionSheet";
import {
  getDocument,
  getDocumentFileUrl,
  updateDocument,
  deleteDocument,
  type DocumentOut,
  type ExtractedInvoice,
} from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Envoyé",
  queued: "En file d'attente",
  processing: "Extraction en cours…",
  needs_review: "À vérifier",
  done: "Terminé",
  failed: "Échec de l'extraction",
};

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [fileContentType, setFileContentType] = useState<string | null>(null);
  const [fileGone, setFileGone] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let poll: ReturnType<typeof setInterval> | null = null;

    const load = async () => {
      try {
        const d = await getDocument(id);
        setDoc(d);
        if (d.status === "processing" || d.status === "queued") {
          if (!poll) poll = setInterval(load, 2000);
        } else if (poll) {
          clearInterval(poll);
          poll = null;
        }
      } catch (e: any) {
        setError(e.message);
      }
    };
    load();

    return () => { if (poll) clearInterval(poll); };
  }, [id]);

  useEffect(() => {
    if (!doc || doc.status === "queued" || doc.status === "processing") return;
    getDocumentFileUrl(id)
      .then((res) => {
        if (res === null) {
          setFileGone(true);
        } else {
          setFileUrl(res.url);
          setFileContentType(res.content_type);
        }
      })
      .catch(() => { /* aperçu indisponible — pas bloquant */ });
  }, [doc, id]);

  const save = async (next: ExtractedInvoice) => {
    if (!doc) return;
    setDoc({ ...doc, extracted_data: next });
    setSaving(true);
    try {
      await updateDocument(doc.id, next);
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!doc || !confirm("Supprimer définitivement ce document et sa fiche extraite ?")) return;
    try {
      await deleteDocument(doc.id);
      router.push("/");
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (error && !doc) {
    return (
      <main className="max-w-3xl mx-auto px-5 py-10">
        <p className="text-sm text-orange-800 bg-orange-100 rounded-lg px-3 py-2">{error}</p>
        <Link href="/" className="text-accent underline underline-offset-2 text-sm mt-4 inline-block">
          ← Retour à l'historique
        </Link>
      </main>
    );
  }

  if (!doc) {
    return <main className="max-w-3xl mx-auto px-5 py-10 text-sm text-ink/60">Chargement…</main>;
  }

  return (
    <main className="max-w-3xl mx-auto px-5 py-10 pb-20">
      <Link href="/" className="text-accent underline underline-offset-2 text-sm">← Retour à l'historique</Link>

      <div className="flex justify-between items-start mt-4 mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl mb-1">{doc.original_filename}</h1>
          <p className="text-sm text-ink/60">
            {STATUS_LABEL[doc.status] ?? doc.status}
            {saving && " · enregistrement…"}
            {saved && " · enregistré ✓"}
          </p>
        </div>
        <button onClick={remove} className="text-sm text-orange-800 hover:bg-orange-100 rounded-lg px-3 py-1.5">
          Supprimer
        </button>
      </div>

      {error && <p className="mb-4 text-sm text-orange-800 bg-orange-100 rounded-lg px-3 py-2">{error}</p>}

      {(doc.status === "queued" || doc.status === "processing") && (
        <div className="flex items-center gap-3 bg-paper-raised border border-rule/60 rounded-2xl p-6 text-sm text-ink/60">
          <span className="w-3.5 h-3.5 rounded-full border-2 border-rule border-t-accent animate-spin" />
          Extraction en cours — cette page se met à jour automatiquement.
        </div>
      )}

      {doc.status === "failed" && (
        <div className="bg-orange-100 text-orange-800 rounded-2xl p-6 text-sm">
          L'extraction a échoué{doc.error_message ? ` : ${doc.error_message}` : "."}
        </div>
      )}

      <div className="grid sm:grid-cols-[220px_1fr] gap-6 items-start">
        <div className="bg-paper-raised border border-rule/60 rounded-2xl p-3">
          {fileUrl && fileContentType?.startsWith("image/") && (
            <img src={fileUrl} alt="Document original" className="w-full rounded-lg" />
          )}
          {fileUrl && fileContentType === "application/pdf" && (
            <a href={fileUrl} target="_blank" rel="noreferrer" className="block text-center text-sm text-accent underline underline-offset-2 py-8">
              Ouvrir le PDF original
            </a>
          )}
          {fileGone && (
            <p className="text-xs text-ink/60 p-3">
              Fichier original supprimé après le délai de rétention. Les données extraites restent disponibles.
            </p>
          )}
          {!fileUrl && !fileGone && doc.status !== "queued" && doc.status !== "processing" && (
            <p className="text-xs text-ink/60 p-3">Aperçu indisponible.</p>
          )}
        </div>

        <div>
          {doc.extracted_data && (
            <ExtractionSheet value={doc.extracted_data} onChange={save} />
          )}
        </div>
      </div>
    </main>
  );
}
