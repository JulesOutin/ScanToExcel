"use client";

import { useRef, useState } from "react";

export function UploadZone({ onFile, disabled }: { onFile: (f: File) => void; disabled?: boolean }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
      className={`border-[1.5px] border-dashed rounded-2xl p-8 text-center cursor-pointer transition-colors
        ${dragging ? "border-accent bg-emerald-50" : "border-rule"}
        ${disabled ? "opacity-50 pointer-events-none" : ""}`}
    >
      <span className="block text-2xl mb-2">🧾</span>
      <p><strong className="font-semibold">Glisse une facture ici</strong>, ou clique pour choisir</p>
      <p className="mt-1 text-xs font-mono text-ink/60">PDF · JPG · PNG · WEBP</p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
    </div>
  );
}
