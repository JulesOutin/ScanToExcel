import type { Metadata } from "next";
import "./globals.css";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://scantoexcel.fr";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "ScanToExcel — Facture reçue, données prêtes",
    template: "%s · ScanToExcel",
  },
  description:
    "Convertis tes factures PDF et images en tableur Excel ou export comptable (FEC), avec vérification SIRET/TVA intégrée.",
  openGraph: {
    type: "website",
    locale: "fr_FR",
    siteName: "ScanToExcel",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="font-sans">{children}</body>
    </html>
  );
}
