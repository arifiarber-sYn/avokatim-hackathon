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

export const metadata: Metadata = {
  title: "AvokatIM",
  description: "Modern legal practice management",
  appleWebApp: { capable: true, title: "AvokatIM", statusBarStyle: "default" },
  icons: { apple: "/icons/apple-touch-icon.png" },
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
        <I18nProvider>{children}</I18nProvider>
        {UMAMI_SRC && UMAMI_ID && (
          <script defer src={UMAMI_SRC} data-website-id={UMAMI_ID} />
        )}
      </body>
    </html>
  );
}
