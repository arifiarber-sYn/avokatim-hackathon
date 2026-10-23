import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sa kushton një proces gjyqësor në Kosovë? — Kalkulatori i kostos",
  description:
    "Llogarit falas taksën gjyqësore sipas Udhëzimit Administrativ të " +
    "KGJK-së (në fuqi nga 1 janari 2026) dhe tarifat e avokatëve sipas " +
    "Tarifës së OAK-së — rreziku i kostos nëpër tri instancat, sipas " +
    "parimit «humbësi paguan» të LPK-së.",
  alternates: { canonical: "/kostoja" },
};

export default function KostojaLayout({ children }: { children: React.ReactNode }) {
  return children;
}
