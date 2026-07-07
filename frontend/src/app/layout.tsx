import type { Metadata } from "next";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "BoraLaw",
  description: "Modern legal practice management",
  appleWebApp: { capable: true, title: "BoraLaw", statusBarStyle: "default" },
  icons: { apple: "/icons/apple-touch-icon.png" },
};

export const viewport = {
  themeColor: "#4338ca",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sq">
      <body className="antialiased bg-slate-50 text-slate-900">
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}
