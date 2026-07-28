import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Llogaritësi i afateve ligjore të Kosovës",
  description:
    "Llogarit falas afatin për ankesë, padi a kundërshtim sipas ligjeve të " +
    "Kosovës (LPK, LPP, LPA) — me ditët e festave zyrtare të përfshira dhe " +
    "bazën ligjore të cituar për çdo afat.",
  alternates: { canonical: "/afatet" },
};

export default function AfatetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
