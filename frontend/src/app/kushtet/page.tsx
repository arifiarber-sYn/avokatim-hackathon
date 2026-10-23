"use client";

import { LegalPage } from "@/components/legal-page";
import { TOS } from "@/lib/legal";

export default function TermsPage() {
  return <LegalPage docs={TOS} />;
}
