import type { Metadata } from "next";
import { serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Für Anwälte — die digitale Kanzlei mit KI und neuen Mandaten"
      : "Për avokatët — zyra digjitale me AI dhe klientë të rinj",
    description: de
      ? "Akten mit automatischen Fristen, RVG-Abrechnung mit E-Rechnung und " +
        "DATEV-Export, der Ava Agent, der Ziele in genehmigte Schritte umsetzt, " +
        "proaktive KI mit Morgen-Briefing und Rechtsprechungs-Monitor, und neue " +
        "Mandate aus dem öffentlichen Marktplatz. 3 Monate kostenlos, dann " +
        "39 €/Nutzer/Monat — keine Mindestlaufzeit, nie eine Provision."
      : "Lëndët me afate automatike sipas LPK/LPP/LPA, Ava Agjente që kthen " +
        "qëllimet në hapa me aprovim, AI proaktive me briefing mëngjesi dhe " +
        "monitorim të praktikës gjyqësore, dhe raste të reja nga tregu publik. " +
        "Viti i parë falas, pastaj çmim fiks — kurrë përqindje.",
    alternates: { canonical: "/per-avokatet" },
  };
}

export default function PerAvokatetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
