import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Për avokatët — zyra digjitale me AI dhe klientë të rinj",
  description:
    "Lëndët me afate automatike sipas LPK/LPP/LPA, dokumente me AI, faturim, " +
    "asistentja Ava me ligjet e plota të Kosovës dhe raste të reja nga tregu " +
    "publik. Viti i parë falas, pastaj çmim fiks — kurrë përqindje.",
  alternates: { canonical: "/per-avokatet" },
};

export default function PerAvokatetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
