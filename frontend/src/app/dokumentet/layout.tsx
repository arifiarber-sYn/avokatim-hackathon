import type { Metadata } from "next";
import { serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Einfache Rechtsdokumente kostenlos erstellen"
      : "Gjenero shkresa dhe ankesa ligjore falas",
    description: de
      ? "Kostenloser Generator für einfache Rechtsdokumente: Widersprüche, " +
        "Anträge, Vollmachten und weitere Schreiben — mit Ihren Daten ausgefüllt " +
        "und zum Download bereit."
      : "Gjenerator falas i shkresave ligjore për Kosovën: ankesa, kërkesa, " +
        "autorizime dhe parashtresa të tjera — të plotësuara me të dhënat e tua " +
        "dhe gati për shkarkim.",
    alternates: { canonical: "/dokumentet" },
  };
}

export default function DokumentetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
