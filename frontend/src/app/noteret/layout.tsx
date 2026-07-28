import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Noterët e licencuar në Kosovë — drejtoria dhe tarifat zyrtare",
  description:
    "Drejtoria e plotë e noterëve të licencuar nga regjistri publik i ONK-së, " +
    "me adresa dhe kontakte sipas qytetit. Llogaritë tarifën zyrtare dhe " +
    "dokumentet e nevojshme për çdo akt noterial — falas.",
  alternates: { canonical: "/noteret" },
};

interface PublicNotary {
  name: string;
  phone: string | null;
  address: string | null;
  city: string | null;
}

/** ItemList of Notary entries from the official ONK registry (GEO —
 * see avokatet/layout.tsx). Emails are deliberately omitted: this is a
 * crawler-facing block and would turn the registry into a spam list. */
async function notaryJsonLd(): Promise<string | null> {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/public/tools/notaries", {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    const data: { notaries: PublicNotary[] } = await res.json();
    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Noterët e licencuar në Kosovë",
      numberOfItems: data.notaries.length,
      itemListElement: data.notaries.map((n, i) => ({
        "@type": "ListItem",
        position: i + 1,
        item: {
          "@type": "Notary",
          name: n.name,
          telephone: n.phone || undefined,
          address: n.city
            ? {
                "@type": "PostalAddress",
                streetAddress: n.address || undefined,
                addressLocality: n.city,
                addressCountry: "XK",
              }
            : undefined,
        },
      })),
    });
  } catch {
    return null;
  }
}

export default async function NoteretLayout({ children }: { children: React.ReactNode }) {
  const jsonLd = await notaryJsonLd();
  return (
    <>
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd }} />
      )}
      {children}
    </>
  );
}
