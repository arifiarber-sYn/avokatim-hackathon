import type { Metadata } from "next";
import { dictionaries } from "@/lib/dictionaries";
import { serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Kostenlose Rechtshilfe für Bürger"
      : "Ndihmë ligjore falas për qytetarët e Kosovës",
    description: de
      ? "Fragen Sie Ava zu deutschen Gesetzen, stellen Sie Ihren Fall ein, damit " +
        "Anwälte sich bei Ihnen melden, berechnen Sie Fristen und erstellen Sie " +
        "einfache Rechtsdokumente — alles kostenlos."
      : "Pyet Avën për çdo ligj të Kosovës, posto rastin tënd që avokatët të të " +
        "kontaktojnë, llogarit afatet procedurale dhe gjenero shkresa — gjithçka " +
        "falas. Në urgjencë, butoni SOS të lidh me avokat kujdestar.",
    alternates: { canonical: "/per-qytetaret" },
  };
}

// FAQPage schema sourced from the same dictionary entries the page renders,
// so the structured data can never drift from the visible answers. Each host
// serves the schema in its own default language (sq for XK, de for DE).
function faqJsonLd(locale: "sq" | "de") {
  const dict = dictionaries[locale] as unknown as Record<string, string>;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [1, 2, 3, 4, 5, 6].map((n) => ({
      "@type": "Question",
      name: dict[`faqQ${n}`],
      acceptedAnswer: { "@type": "Answer", text: dict[`faqA${n}`] },
    })),
  };
}

export default async function PerQytetaretLayout({ children }: { children: React.ReactNode }) {
  const locale = (await serverCountry()) === "DE" ? "de" : "sq";
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd(locale)) }}
      />
      {children}
    </>
  );
}
