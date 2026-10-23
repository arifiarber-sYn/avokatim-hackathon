"use client";

import { LegalPage } from "@/components/legal-page";
import { PRIVACY } from "@/lib/legal";

export default function PrivacyPage() {
  return <LegalPage docs={PRIVACY} />;
}
