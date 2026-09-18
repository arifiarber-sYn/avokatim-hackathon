"use client";

// Citation verification badges (D-059 F6): after an answer finishes, the
// backend checks every cited §/nen/case number against the indexed corpus
// and streams a `citation_check` event. Rendered under the answer in the
// assistant page and the slide-over panel.
import { useI18n } from "@/lib/i18n";

export interface CitationCheck {
  cite: string;
  kind: "statute" | "case" | "law";
  status: "verified" | "approx" | "law_found" | "unverified";
  source_title?: string;
  doc_id?: string;
  chunk_id?: string;
  note?: string;
}

const TONE: Record<CitationCheck["status"], string> = {
  verified: "bg-emerald-50 border-emerald-200 text-emerald-700",
  approx: "bg-amber-50 border-amber-200 text-amber-700",
  law_found: "bg-amber-50 border-amber-200 text-amber-700",
  unverified: "bg-slate-50 border-slate-200 text-slate-500",
};
const ICON: Record<CitationCheck["status"], string> = {
  verified: "✓",
  approx: "≈",
  law_found: "§",
  unverified: "?",
};

export default function CitationChecks({
  checks,
  onOpenSource,
}: {
  checks?: CitationCheck[];
  // Set by pages that can show the source (D audit 2026-09-18: clickable
  // citations — opens the corpus doc/chunk behind the badge).
  onOpenSource?: (c: CitationCheck) => void;
}) {
  const { t } = useI18n();
  if (!checks?.length) return null;
  const tooltip = (c: CitationCheck) =>
    c.status === "verified"
      ? `${t.ccVerified}${c.source_title ? ` — ${c.source_title}` : ""}`
      : c.status === "approx"
        ? `${t.ccApprox}${c.note ? ` (${c.note})` : ""}`
        : c.status === "law_found"
          ? t.ccLawFound
          : `${t.ccUnverified}${c.note ? ` (${c.note})` : ""}`;
  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      <span className="text-[11px] text-slate-400">{t.ccTitle}</span>
      {checks.map((c) => {
        const clickable = Boolean(onOpenSource && c.doc_id);
        const cls = `text-[11px] rounded-full px-2 py-0.5 border ${TONE[c.status]}${
          clickable ? " cursor-pointer hover:underline" : ""
        }`;
        return clickable ? (
          <button
            key={c.cite}
            type="button"
            title={tooltip(c)}
            className={cls}
            onClick={() => onOpenSource!(c)}
          >
            {ICON[c.status]} {c.cite}
          </button>
        ) : (
          <span key={c.cite} title={tooltip(c)} className={cls}>
            {ICON[c.status]} {c.cite}
          </span>
        );
      })}
    </div>
  );
}
