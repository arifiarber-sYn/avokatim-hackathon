import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import type { Country } from "@/lib/country";
import { I18nProvider } from "@/lib/i18n";
import { COUNTRY_BASE_URL, serverCountry } from "@/lib/seo";
import ErrorReporter from "@/components/error-reporter";

// Self-hosted at build time by next/font — no runtime requests to Google.
// latin-ext covers Albanian (ë, ç) and the Balkan languages.
const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
  display: "swap",
});

// GEO/SEO: AI assistants (ChatGPT, Perplexity, AI Overviews) build lawyer
// shortlists from structured metadata — titles, descriptions and the JSON-LD
// below are what gets us cited when someone asks "avokat në Prishtinë" or
// "Anwalt in Berlin". Everything is per-country (D-039): the DE host must
// present itself in German, the XK host in Albanian.
export async function generateMetadata(): Promise<Metadata> {
  const country = await serverCountry();
  const base = COUNTRY_BASE_URL[country];
  const de = country === "DE";
  const title = de
    ? "AvokatIM — Kostenlose Rechtshilfe mit KI und geprüften Anwälten in Deutschland"
    : "AvokatIM — Ndihmë ligjore falas me AI dhe avokatë të verifikuar në Kosovë";
  const description = de
    ? "Die Rechtsplattform: KI-Assistentin Ava beantwortet Rechtsfragen kostenlos " +
      "auf Basis deutscher Gesetze, geprüfte Anwälte im Verzeichnis, und die " +
      "digitale Kanzlei mit KI für Profis."
    : "Platforma ligjore e Kosovës: asistentja Ava me ligjet e plota të Kosovës falas " +
      "për qytetarët, drejtoria e avokatëve dhe noterëve të verifikuar, dhe zyra " +
      "digjitale me AI për profesionistët.";
  return {
    metadataBase: new URL(base),
    title: { default: title, template: "%s · AvokatIM" },
    description,
    appleWebApp: { capable: true, title: "AvokatIM", statusBarStyle: "default" },
    icons: { apple: "/icons/apple-touch-icon.png" },
    openGraph: {
      type: "website",
      siteName: "AvokatIM",
      locale: de ? "de_DE" : "sq_AL",
      url: base,
      title,
      description: de
        ? "Fragen Sie Ava kostenlos zu deutschen Gesetzen, finden Sie einen " +
          "geprüften Anwalt oder stellen Sie Ihren Fall ein — Anwälte melden sich bei Ihnen."
        : "Pyet Avën për ligjet e Kosovës falas, gjej avokat a noter të verifikuar, " +
          "ose poste rastin tënd — avokatët të kontaktojnë ty.",
    },
    alternates: { canonical: "/" },
  };
}

// Organization + WebSite JSON-LD: the identity block AI crawlers look for.
function orgJsonLd(country: Country) {
  const base = COUNTRY_BASE_URL[country];
  const de = country === "DE";
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${base}/#org`,
        name: "AvokatIM",
        url: base,
        logo: `${base}/icons/apple-touch-icon.png`,
        description: de
          ? "Die Rechtsplattform, die Bürger mit geprüften Anwälten verbindet — " +
            "mit kostenloser KI-Assistentin auf Basis deutscher Gesetze."
          : "Platforma ligjore e Kosovës që lidh qytetarët me avokatë dhe noterë " +
            "të verifikuar, me asistente AI falas mbi ligjet e Kosovës.",
        areaServed: { "@type": "Country", name: de ? "Germany" : "Kosovo" },
        knowsLanguage: de
          ? ["de", "en", "tr", "sq", "sr", "bs", "zh"]
          : ["sq", "en", "sr", "tr", "bs", "zh"],
      },
      {
        "@type": "WebSite",
        "@id": `${base}/#website`,
        url: base,
        name: "AvokatIM",
        publisher: { "@id": `${base}/#org` },
        inLanguage: de ? "de" : "sq",
      },
    ],
  };
}

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

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const country = await serverCountry();
  return (
    <html lang={country === "DE" ? "de" : "sq"} className={inter.variable}>
      <body className="antialiased bg-slate-50 text-slate-900">
        {/* Apply the saved theme before paint — no light flash (D-054 F5) */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{var p=localStorage.getItem('avokatim-theme');var d=p==='dark'||(p==='system'&&matchMedia('(prefers-color-scheme: dark)').matches);if(d)document.documentElement.classList.add('theme-dark')}catch(e){}",
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd(country)) }}
        />
        <I18nProvider>{children}</I18nProvider>
        <ErrorReporter />
        {UMAMI_SRC && UMAMI_ID && (
          <script defer src={UMAMI_SRC} data-website-id={UMAMI_ID} />
        )}
      </body>
    </html>
  );
}
