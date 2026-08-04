"use client";

// Citation verification badges (D-059 F6): after an answer finishes, the
// backend checks every cited §/nen/case number against the indexed corpus
// and streams a `citation_check` event. Rendered under the answer in the
// assistant page and the slide-over panel.
import { useI18n } from "@/lib/i18n";

export interface CitationCheck {
  cite: string;
  kind: "statute" | "case" | "law";
  status: "verified" | "law_found" | "unverified";
  source_title?: string;
}

export default function CitationChecks({ checks }: { checks?: CitationCheck[] }) {
  const { t } = useI18n();
  if (!checks?.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      <span className="text-[11px] text-slate-400">{t.ccTitle}</span>
      {checks.map((c) => (
        <span
          key={c.cite}
          title={
            c.status === "verified"
              ? `${t.ccVerified}${c.source_title ? ` — ${c.source_title}` : ""}`
              : c.status === "law_found"
                ? t.ccLawFound
                : t.ccUnverified
          }
          className={`text-[11px] rounded-full px-2 py-0.5 border ${
            c.status === "verified"
              ? "bg-emerald-50 border-emerald-200 text-emerald-700"
              : c.status === "law_found"
                ? "bg-amber-50 border-amber-200 text-amber-700"
                : "bg-slate-50 border-slate-200 text-slate-500"
          }`}
        >
          {c.status === "verified" ? "✓" : c.status === "law_found" ? "≈" : "?"} {c.cite}
        </span>
      ))}
    </div>
  );
}
