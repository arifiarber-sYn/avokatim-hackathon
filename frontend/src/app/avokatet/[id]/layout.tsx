import type { Metadata } from "next";

interface ProfileData {
  id: string;
  full_name: string;
  firm_name: string;
  bio: string | null;
  practice_areas: string[];
  cities: string[];
  languages: string[];
  rating: number | null;
  review_count: number;
  years_experience: number | null;
}

async function fetchProfile(id: string): Promise<ProfileData | null> {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/public/lawyers/${id}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Per-lawyer metadata: each profile is its own citable URL — the whole
 * point of the dedicated page (GEO: AI assistants cite specific URLs). */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const p = await fetchProfile(id);
  if (!p) return { title: "Avokat — AvokatIM", robots: { index: false } };
  const city = p.cities[0] || "Kosovë";
  return {
    title: `Av. ${p.full_name} — ${city}`,
    description:
      `${p.full_name} (${p.firm_name}) — avokat i verifikuar nga OAK në ${city}` +
      (p.years_experience ? `, ${p.years_experience} vjet përvojë` : "") +
      ". Dërgo rastin ose rezervo konsultë përmes AvokatIM — falas për qytetarët.",
    alternates: { canonical: `/avokatet/${p.id}` },
  };
}

export default async function LawyerProfileLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const p = await fetchProfile(id);
  const jsonLd = p
    ? JSON.stringify({
        "@context": "https://schema.org",
        "@type": "Attorney",
        name: p.full_name,
        url: `https://avokatiim.ai/avokatet/${p.id}`,
        worksFor: { "@type": "Organization", name: p.firm_name },
        description: p.bio || undefined,
        address: p.cities.length
          ? { "@type": "PostalAddress", addressLocality: p.cities[0], addressCountry: "XK" }
          : undefined,
        knowsLanguage: p.languages,
        knowsAbout: p.practice_areas,
        ...(p.rating != null && p.review_count > 0
          ? {
              aggregateRating: {
                "@type": "AggregateRating",
                ratingValue: p.rating,
                reviewCount: p.review_count,
              },
            }
          : {}),
      })
    : null;
  return (
    <>
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd }} />
      )}
      {children}
    </>
  );
}
