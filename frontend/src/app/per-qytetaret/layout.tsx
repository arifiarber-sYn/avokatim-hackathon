import type { Metadata } from "next";
import { dictionaries } from "@/lib/dictionaries";

export const metadata: Metadata = {
  title: "Ndihmë ligjore falas për qytetarët e Kosovës",
  description:
    "Pyet Avën për çdo ligj të Kosovës, posto rastin tënd që avokatët të të " +
    "kontaktojnë, llogarit afatet procedurale dhe gjenero shkresa — gjithçka " +
    "falas. Në urgjencë, butoni SOS të lidh me avokat kujdestar.",
  alternates: { canonical: "/per-qytetaret" },
};

// FAQPage schema sourced from the same dictionary entries the page renders,
// so the structured data can never drift from the visible answers (sq is the
// default locale and what crawlers see first).
const sq = dictionaries.sq as unknown as Record<string, string>;
const FAQ_JSONLD = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [1, 2, 3, 4, 5, 6].map((n) => ({
    "@type": "Question",
    name: sq[`faqQ${n}`],
    acceptedAnswer: { "@type": "Answer", text: sq[`faqA${n}`] },
  })),
};

export default function PerQytetaretLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(FAQ_JSONLD) }}
      />
      {children}
    </>
  );
}
