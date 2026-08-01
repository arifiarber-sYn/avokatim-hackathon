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
        "DATEV-Export, Dokumente mit KI, die Assistentin Ava mit deutschen " +
        "Gesetzen und neue Mandate aus dem öffentlichen Marktplatz."
      : "Lëndët me afate automatike sipas LPK/LPP/LPA, dokumente me AI, faturim, " +
        "asistentja Ava me ligjet e plota të Kosovës dhe raste të reja nga tregu " +
        "publik. Viti i parë falas, pastaj çmim fiks — kurrë përqindje.",
    alternates: { canonical: "/per-avokatet" },
  };
}

export default function PerAvokatetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
