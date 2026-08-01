import type { Metadata } from "next";
import type { Country } from "@/lib/country";
import { COUNTRY_BASE_URL, serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Geprüfte Anwälte in Deutschland — das öffentliche Verzeichnis"
      : "Avokatët e verifikuar në Kosovë — drejtoria publike",
    description: de
      ? "Finden Sie einen zugelassenen Anwalt nach Rechtsgebiet, Stadt und " +
        "Sprache. Mandantenbewertungen, transparente Profile und direkter " +
        "Kontakt — kostenlos für Bürger."
      : "Gjej avokat të verifikuar nga Oda e Avokatëve të Kosovës sipas fushës, " +
        "qytetit dhe gjuhës. Recensione klientësh, çmime transparente dhe kontakt " +
        "i drejtpërdrejtë — falas për qytetarët.",
    alternates: { canonical: "/avokatet" },
  };
}

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
 * so crawlers that don't execute JS still see it; refreshed hourly. The
 * country header keeps each host's list scoped to its own lawyers (D-034). */
async function directoryJsonLd(country: Country): Promise<string | null> {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/public/lawyers", {
      headers: { "x-avokatim-country": country },
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const lawyers: PublicLawyer[] = await res.json();
    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      name:
        country === "DE"
          ? "Geprüfte Anwälte bei AvokatIM"
          : "Avokatët e verifikuar në AvokatIM",
      numberOfItems: lawyers.length,
      itemListElement: lawyers.map((l, i) => ({
        "@type": "ListItem",
        position: i + 1,
        item: {
          "@type": "Attorney",
          name: l.firm_name || l.full_name,
          url: `${COUNTRY_BASE_URL[country]}/avokatet`,
          address: l.cities.length
            ? { "@type": "PostalAddress", addressLocality: l.cities[0], addressCountry: country }
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
  const jsonLd = await directoryJsonLd(await serverCountry());
  return (
    <>
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd }} />
      )}
      {children}
    </>
  );
}
