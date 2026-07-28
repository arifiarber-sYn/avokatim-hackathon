import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Avokatët e verifikuar në Kosovë — drejtoria publike",
  description:
    "Gjej avokat të verifikuar nga Oda e Avokatëve të Kosovës sipas fushës, " +
    "qytetit dhe gjuhës. Recensione klientësh, çmime transparente dhe kontakt " +
    "i drejtpërdrejtë — falas për qytetarët.",
  alternates: { canonical: "/avokatet" },
};

interface PublicLawyer {
  full_name: string;
  firm_name: string | null;
  cities: string[];
  languages: string[];
  practice_areas: string[];
  verified: boolean;
  rating: number | null;
  review_count: number;
}

/** ItemList of Attorney entries — the structured data AI search assistants
 * read when building "lawyer in Prishtinë" shortlists (GEO). Server-rendered
 * so crawlers that don't execute JS still see it; refreshed hourly. */
async function directoryJsonLd(): Promise<string | null> {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/public/lawyers", {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const lawyers: PublicLawyer[] = await res.json();
    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Avokatët e verifikuar në AvokatIM",
      numberOfItems: lawyers.length,
      itemListElement: lawyers.map((l, i) => ({
        "@type": "ListItem",
        position: i + 1,
        item: {
          "@type": "Attorney",
          name: l.firm_name || l.full_name,
          url: "https://avokatiim.ai/avokatet",
          address: l.cities.length
            ? { "@type": "PostalAddress", addressLocality: l.cities[0], addressCountry: "XK" }
            : undefined,
          knowsLanguage: l.languages,
          knowsAbout: l.practice_areas,
          ...(l.rating != null && l.review_count > 0
            ? {
                aggregateRating: {
                  "@type": "AggregateRating",
                  ratingValue: l.rating,
                  reviewCount: l.review_count,
                },
              }
            : {}),
        },
      })),
    });
  } catch {
    return null;
  }
}

export default async function AvokatetLayout({ children }: { children: React.ReactNode }) {
  const jsonLd = await directoryJsonLd();
  return (
    <>
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd }} />
      )}
      {children}
    </>
  );
}
