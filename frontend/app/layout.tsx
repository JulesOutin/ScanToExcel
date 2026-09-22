import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScanToExcel",
  description: "Facture reçue, données prêtes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="font-sans">{children}</body>
    </html>
  );
}
