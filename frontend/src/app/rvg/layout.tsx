import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Was kostet ein Anwalt? — RVG- und Prozesskostenrechner",
  description:
    "Kostenlos die gesetzlichen Anwaltsgebühren nach RVG berechnen: " +
    "Geschäftsgebühr, Verfahrens- und Terminsgebühr nach § 13 RVG " +
    "(Stand KostBRÄG 2025) — plus Prozesskostenrisiko mit Gerichtskosten " +
    "(GKG) über alle drei Instanzen.",
  alternates: { canonical: "/rvg" },
};

export default function RvgLayout({ children }: { children: React.ReactNode }) {
  return children;
}
