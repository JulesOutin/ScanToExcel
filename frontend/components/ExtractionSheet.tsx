"use client";

import { useMemo } from "react";
import type { ExtractedInvoice, LineItem } from "@/lib/api";
import { identifyAndCheck } from "@/lib/frenchTaxIds";

function setPath(obj: ExtractedInvoice, path: string, value: string | number): ExtractedInvoice {
  const clone: ExtractedInvoice = JSON.parse(JSON.stringify(obj));
  if (path.startsWith("supplier.")) {
    (clone.supplier as any)[path.split(".")[1]] = value;
  } else {
    (clone as any)[path] = value;
  }
  return clone;
}

function validate(inv: ExtractedInvoice): string[] {
  const warnings: string[] = [];
  if (inv.total && Math.abs(inv.subtotal + inv.tax - inv.total) > 0.02) {
    warnings.push(
      `Sous-total + TVA (${(inv.subtotal + inv.tax).toFixed(2)}) ne correspond pas au total (${inv.total.toFixed(2)}).`
    );
  }
  if (!inv.invoice_number) warnings.push("Numéro de facture manquant.");
  if (!inv.currency || inv.currency.length !== 3) warnings.push("Devise absente ou incorrecte.");
  inv.items.forEach((it, i) => {
    const expected = it.quantity * it.unit_price;
    if (it.total && Math.abs(expected - it.total) > Math.max(0.02, expected * 0.02)) {
      warnings.push(`Ligne ${i + 1} : quantité × prix unitaire ≠ total de ligne.`);
    }
  });
  const taxIdWarning = identifyAndCheck(inv.supplier.registration_number);
  if (taxIdWarning) warnings.push(taxIdWarning);
  return warnings;
}

export function ExtractionSheet({
  value,
  onChange,
}: {
  value: ExtractedInvoice;
  onChange: (next: ExtractedInvoice) => void;
}) {
  const warnings = useMemo(() => validate(value), [value]);
  const confidencePct = Math.round((value.confidence ?? 0) * 100);
  const pillClass =
    confidencePct >= 85 ? "bg-emerald-100 text-emerald-800"
    : confidencePct >= 60 ? "bg-orange-100 text-orange-800"
    : "bg-orange-100 text-orange-800";

  const field = (label: string, path: string, isNum = false, placeholder?: string) => {
    const val = path.startsWith("supplier.")
      ? (value.supplier as any)[path.split(".")[1]]
      : (value as any)[path];
    return (
      <div key={path}>
        <label className="block text-[11px] font-mono text-ink/60 mb-1">{label}</label>
        <input
          value={val ?? ""}
          placeholder={placeholder}
          onChange={(e) => onChange(setPath(value, path, isNum ? Number(e.target.value) || 0 : e.target.value))}
          className={`w-full rounded-md border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:border-accent ${isNum ? "font-mono text-right" : ""}`}
        />
      </div>
    );
  };

  const updateItem = (idx: number, key: keyof LineItem, val: string | number) => {
    const items = [...value.items];
    items[idx] = { ...items[idx], [key]: val };
    onChange({ ...value, items });
  };
  const removeItem = (idx: number) => {
    onChange({ ...value, items: value.items.filter((_, i) => i !== idx) });
  };
  const addItem = () => {
    onChange({ ...value, items: [...value.items, { description: "", quantity: 1, unit_price: 0, tax_rate: 0, total: 0 }] });
  };

  return (
    <div className="bg-paper-raised border border-rule/60 rounded-2xl p-6">
      <div className="flex justify-between items-start mb-4 gap-3">
        <div>
          <h2 className="font-display text-lg">Fiche extraite</h2>
          <p className="text-sm text-ink/60 m-0">Corrige les champs avant d'ajouter au lot.</p>
        </div>
        <span className={`font-mono text-xs px-2.5 py-1 rounded-full whitespace-nowrap ${pillClass}`}>
          Confiance : {confidencePct} %
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-2">
        {field("Fournisseur", "supplier.name")}
        {field("N° TVA / SIRET", "supplier.registration_number")}
        <div className="col-span-2">{field("Adresse", "supplier.address")}</div>
        {field("N° de facture", "invoice_number")}
        {field("Devise", "currency")}
        {field("Date de facture", "invoice_date", false, "AAAA-MM-JJ")}
        {field("Échéance", "due_date", false, "AAAA-MM-JJ")}
        {field("Sous-total HT", "subtotal", true)}
        {field("TVA / Taxe", "tax", true)}
        {field("Total TTC", "total", true)}
      </div>

      {warnings.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {warnings.map((w, i) => (
            <li key={i} className="text-sm text-orange-800 bg-orange-100 rounded-lg px-2.5 py-2">⚠ {w}</li>
          ))}
        </ul>
      )}

      <hr className="my-5 border-rule/50" />

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left font-mono text-[11px] text-ink/60 border-b border-rule">
            <th className="pb-2">Description</th>
            <th className="pb-2">Qté</th>
            <th className="pb-2">Prix unit.</th>
            <th className="pb-2">TVA %</th>
            <th className="pb-2">Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {value.items.map((it, idx) => (
            <tr key={idx} className="border-b border-rule/40">
              <td><input value={it.description} onChange={(e) => updateItem(idx, "description", e.target.value)} className="w-full bg-transparent px-1 py-1.5" /></td>
              <td><input value={it.quantity} onChange={(e) => updateItem(idx, "quantity", Number(e.target.value) || 0)} className="w-full bg-transparent px-1 py-1.5 font-mono text-right" /></td>
              <td><input value={it.unit_price} onChange={(e) => updateItem(idx, "unit_price", Number(e.target.value) || 0)} className="w-full bg-transparent px-1 py-1.5 font-mono text-right" /></td>
              <td><input value={it.tax_rate} onChange={(e) => updateItem(idx, "tax_rate", Number(e.target.value) || 0)} className="w-full bg-transparent px-1 py-1.5 font-mono text-right" /></td>
              <td><input value={it.total} onChange={(e) => updateItem(idx, "total", Number(e.target.value) || 0)} className="w-full bg-transparent px-1 py-1.5 font-mono text-right" /></td>
              <td><button onClick={() => removeItem(idx)} className="text-ink/50 hover:text-orange-700 px-1">✕</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={addItem} className="mt-2 text-accent underline underline-offset-2 text-sm">+ Ajouter une ligne</button>
    </div>
  );
}
