import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";

// Self-hosted at build time by next/font — no runtime requests to Google.
// latin-ext covers Albanian (ë, ç) and the Balkan languages.
const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
  display: "swap",
});

// GEO/SEO: AI assistants (ChatGPT, Perplexity, AI Overviews) build lawyer
// shortlists from structured metadata — titles, descriptions and the JSON-LD
// below are what gets us cited when someone asks "avokat në Prishtinë".
export const metadata: Metadata = {
  metadataBase: new URL("https://avokatiim.ai"),
  title: {
    default: "AvokatIM — Ndihmë ligjore falas me AI dhe avokatë të verifikuar në Kosovë",
    template: "%s · AvokatIM",
  },
  description:
    "Platforma ligjore e Kosovës: asistentja Ava me ligjet e plota të Kosovës falas " +
    "për qytetarët, drejtoria e avokatëve dhe noterëve të verifikuar, dhe zyra " +
    "digjitale me AI për profesionistët.",
  appleWebApp: { capable: true, title: "AvokatIM", statusBarStyle: "default" },
  icons: { apple: "/icons/apple-touch-icon.png" },
  openGraph: {
    type: "website",
    siteName: "AvokatIM",
    locale: "sq_AL",
    url: "https://avokatiim.ai",
    title: "AvokatIM — Ndihmë ligjore falas me AI dhe avokatë të verifikuar",
    description:
      "Pyet Avën për ligjet e Kosovës falas, gjej avokat a noter të verifikuar, " +
      "ose poste rastin tënd — avokatët të kontaktojnë ty.",
  },
  alternates: { canonical: "/" },
};

// Organization + WebSite JSON-LD: the identity block AI crawlers look for.
const ORG_JSONLD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://avokatiim.ai/#org",
      name: "AvokatIM",
      url: "https://avokatiim.ai",
      logo: "https://avokatiim.ai/icons/apple-touch-icon.png",
      description:
        "Platforma ligjore e Kosovës që lidh qytetarët me avokatë dhe noterë " +
        "të verifikuar, me asistente AI falas mbi ligjet e Kosovës.",
      areaServed: { "@type": "Country", name: "Kosovo" },
      knowsLanguage: ["sq", "en", "sr", "tr", "bs", "zh"],
    },
    {
      "@type": "WebSite",
      "@id": "https://avokatiim.ai/#website",
      url: "https://avokatiim.ai",
      name: "AvokatIM",
      publisher: { "@id": "https://avokatiim.ai/#org" },
      inLanguage: "sq",
    },
  ],
};

export const viewport = {
  themeColor: "#4338ca",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover" as const,
};

// Privacy-friendly visit analytics (self-hosted Umami, no cookies).
// Only rendered when both env vars are set at build time.
const UMAMI_SRC = process.env.NEXT_PUBLIC_UMAMI_SRC;
const UMAMI_ID = process.env.NEXT_PUBLIC_UMAMI_ID;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sq" className={inter.variable}>
      <body className="antialiased bg-slate-50 text-slate-900">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(ORG_JSONLD) }}
        />
        <I18nProvider>{children}</I18nProvider>
        {UMAMI_SRC && UMAMI_ID && (
          <script defer src={UMAMI_SRC} data-website-id={UMAMI_ID} />
        )}
      </body>
    </html>
  );
}
