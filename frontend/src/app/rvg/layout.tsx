import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Was kostet ein Anwalt? — RVG-Rechner",
  description:
    "Kostenlos die gesetzlichen Anwaltsgebühren nach RVG berechnen: " +
    "Geschäftsgebühr, Verfahrens- und Terminsgebühr nach § 13 RVG " +
    "(Stand KostBRÄG 2025) — mit Anrechnung und Auslagenpauschale.",
  alternates: { canonical: "/rvg" },
};

export default function RvgLayout({ children }: { children: React.ReactNode }) {
  return children;
}
