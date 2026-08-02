"use client";

// DE rebrand (D-056): the wordmark is country data — "Ava Legal" on the
// German host, "AvokatIM" everywhere else. One component keeps the split
// coloring consistent with each site area's palette. Resolved after mount
// (same pattern as isDE elsewhere) so SSR/hydration stay in sync.
import { useEffect, useState } from "react";
import { clientCountry } from "@/lib/country";

export default function Brand({ accentClass }: { accentClass?: string }) {
  const [de, setDe] = useState(false);
  useEffect(() => setDe(clientCountry() === "DE"), []);
  if (de) {
    return (
      <>
        Ava<span className={accentClass}>&nbsp;Legal</span>
      </>
    );
  }
  return (
    <>
      Avokat<span className={accentClass}>IM</span>
    </>
  );
}
