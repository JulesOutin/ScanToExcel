/**
 * i18n minimal pour la landing page publique (la plus haute valeur SEO).
 * Locale choisie via ?lang=en (défaut : fr) plutôt que des sous-chemins
 * /en/* — un choix volontairement simple pour cette V1 ; une localisation
 * complète de l'app authentifiée reste à faire si le besoin se confirme.
 */
export type Locale = "fr" | "en";

export function resolveLocale(lang?: string): Locale {
  return lang === "en" ? "en" : "fr";
}

interface Dict {
  metaTitle: string;
  metaDescription: string;
  kicker: string;
  heroLine1: string;
  heroEmphasis: string;
  heroSub: string;
  ctaPrimary: string;
  ctaSecondary: string;
  featuresTitle: string;
  features: { title: string; body: string }[];
  fecTitle: string;
  fecBody: string;
  footerNote: string;
}

export const DICTIONARIES: Record<Locale, Dict> = {
  fr: {
    metaTitle: "ScanToExcel — Facture reçue, données prêtes",
    metaDescription:
      "Convertis tes factures PDF et images en tableur Excel ou export comptable (FEC), avec vérification SIRET/TVA intégrée. Essai gratuit, 20 pages/mois.",
    kicker: "SCANTOEXCEL",
    heroLine1: "Une facture entre,",
    heroEmphasis: "un tableur sort.",
    heroSub:
      "Dépose une facture PDF ou image, vérifie les données extraites, exporte en Excel, CSV ou au format comptable FEC — compatible Pennylane, Sage, QuickBooks, Indy.",
    ctaPrimary: "Essayer gratuitement",
    ctaSecondary: "Se connecter",
    featuresTitle: "Pensé pour la compta française",
    features: [
      { title: "Extraction assistée par IA", body: "Fournisseur, montants, TVA, lignes de détail — relus et corrigibles avant export." },
      { title: "SIRET / TVA vérifiés", body: "Contrôle automatique de la clé de Luhn et de la clé de TVA intracommunautaire dès l'extraction." },
      { title: "Export comptable FEC", body: "Le format standard de l'administration fiscale française, importable dans ton logiciel de compta." },
      { title: "Hébergement et rétention maîtrisés", body: "Les fichiers originaux sont supprimés automatiquement après traitement." },
    ],
    fecTitle: "Compatible avec ton logiciel comptable",
    fecBody:
      "L'export FEC (Fichier des Écritures Comptables) est le format d'échange standardisé par l'administration fiscale française — il s'importe tel quel dans Pennylane, Sage, QuickBooks, Indy et la plupart des logiciels de comptabilité.",
    footerNote: "Prototype public — extraction assistée par IA, à vérifier avant tout usage comptable.",
  },
  en: {
    metaTitle: "ScanToExcel — Invoice in, spreadsheet out",
    metaDescription:
      "Turn PDF and image invoices into an Excel spreadsheet or a French accounting export (FEC), with built-in SIRET/VAT validation. Free tier, 20 pages/month.",
    kicker: "SCANTOEXCEL",
    heroLine1: "An invoice goes in,",
    heroEmphasis: "a spreadsheet comes out.",
    heroSub:
      "Drop a PDF or image invoice, check the extracted data, export to Excel, CSV, or the French FEC accounting format — compatible with Pennylane, Sage, QuickBooks, Indy.",
    ctaPrimary: "Try it free",
    ctaSecondary: "Sign in",
    featuresTitle: "Built for French accounting",
    features: [
      { title: "AI-assisted extraction", body: "Supplier, amounts, VAT, line items — reviewable and editable before export." },
      { title: "SIRET / VAT checked", body: "Automatic Luhn checksum and intra-EU VAT key validation right at extraction time." },
      { title: "FEC accounting export", body: "France's standardized tax-authority format, importable straight into your accounting software." },
      { title: "Controlled retention", body: "Original files are deleted automatically after processing." },
    ],
    fecTitle: "Works with your accounting software",
    fecBody:
      "The FEC export (Fichier des Écritures Comptables) is the standardized exchange format mandated by the French tax authority — it imports as-is into Pennylane, Sage, QuickBooks, Indy, and most accounting software.",
    footerNote: "Public prototype — AI-assisted extraction, verify before any accounting use.",
  },
};
