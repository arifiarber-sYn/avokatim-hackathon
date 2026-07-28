import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ndihmë ligjore falas për qytetarët e Kosovës",
  description:
    "Pyet Avën për çdo ligj të Kosovës, posto rastin tënd që avokatët të të " +
    "kontaktojnë, llogarit afatet procedurale dhe gjenero shkresa — gjithçka " +
    "falas. Në urgjencë, butoni SOS të lidh me avokat kujdestar.",
  alternates: { canonical: "/per-qytetaret" },
};

export default function PerQytetaretLayout({ children }: { children: React.ReactNode }) {
  return children;
}
