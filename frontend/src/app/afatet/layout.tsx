import type { Metadata } from "next";
import { serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Fristenrechner — gesetzliche Fristen nach deutschem Recht"
      : "Llogaritësi i afateve ligjore të Kosovës",
    description: de
      ? "Berechnen Sie kostenlos Fristen für Berufung, Klage oder Einspruch nach " +
        "deutschem Recht (ZPO, VwGO) — mit Feiertagen des jeweiligen Bundeslands " +
        "und zitierter Rechtsgrundlage für jede Frist."
      : "Llogarit falas afatin për ankesë, padi a kundërshtim sipas ligjeve të " +
        "Kosovës (LPK, LPP, LPA) — me ditët e festave zyrtare të përfshira dhe " +
        "bazën ligjore të cituar për çdo afat.",
    alternates: { canonical: "/afatet" },
  };
}

export default function AfatetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
