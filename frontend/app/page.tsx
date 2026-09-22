import Link from "next/link";
import type { Metadata } from "next";
import { DICTIONARIES, resolveLocale } from "@/lib/i18n";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://scantoexcel.fr";

export async function generateMetadata({
  searchParams,
}: {
  searchParams: { lang?: string };
}): Promise<Metadata> {
  const locale = resolveLocale(searchParams.lang);
  const t = DICTIONARIES[locale];
  return {
    title: t.metaTitle,
    description: t.metaDescription,
    alternates: {
      canonical: locale === "fr" ? "/" : "/?lang=en",
      languages: { fr: "/", en: "/?lang=en" },
    },
    openGraph: { title: t.metaTitle, description: t.metaDescription },
  };
}

export default function LandingPage({ searchParams }: { searchParams: { lang?: string } }) {
  const locale = resolveLocale(searchParams.lang);
  const t = DICTIONARIES[locale];
  const otherLocale = locale === "fr" ? "en" : "fr";
  const otherHref = otherLocale === "fr" ? "/" : "/?lang=en";

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "ScanToExcel",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description: t.metaDescription,
    offers: { "@type": "Offer", price: "0", priceCurrency: "EUR" },
    url: SITE_URL,
  };

  return (
    <main className="max-w-3xl mx-auto px-5 py-10 pb-20">
      {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <nav className="flex justify-between items-center mb-10 text-sm">
        <span className="font-mono text-xs text-ink/60">{t.kicker}</span>
        <div className="flex gap-4 items-center">
          <Link href={otherHref} hrefLang={otherLocale} className="text-ink/60 hover:text-ink">
            {otherLocale === "en" ? "EN" : "FR"}
          </Link>
          <Link href="/login" className="text-ink/70 hover:text-ink">{t.ctaSecondary}</Link>
        </div>
      </nav>

      <header className="mb-10">
        <h1 className="font-display font-bold text-4xl sm:text-5xl leading-tight mb-4">
          {t.heroLine1}
          <br />
          <em className="italic font-medium text-accent">{t.heroEmphasis}</em>
        </h1>
        <p className="max-w-[52ch] text-lg text-ink/70 mb-6">{t.heroSub}</p>
        <Link
          href="/login"
          className="inline-block bg-accent text-white rounded-lg px-5 py-3 text-sm font-medium"
        >
          {t.ctaPrimary}
        </Link>
      </header>

      <section className="mb-10">
        <h2 className="font-display text-xl mb-4">{t.featuresTitle}</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {t.features.map((f) => (
            <div key={f.title} className="bg-paper-raised border border-rule/60 rounded-2xl p-5">
              <h3 className="font-medium mb-1">{f.title}</h3>
              <p className="text-sm text-ink/70">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-paper-raised border border-rule/60 rounded-2xl p-6 mb-10">
        <h2 className="font-display text-lg mb-2">{t.fecTitle}</h2>
        <p className="text-sm text-ink/70">{t.fecBody}</p>
      </section>

      <footer className="text-xs text-ink/50 font-mono">{t.footerNote}</footer>
    </main>
  );
}
