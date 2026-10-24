"use client";

// Gjurmë arsyetimi (B3, plani i garës 22.10.2026): për çdo përgjigje, UI-ja
// shfaq zinxhirin pyetje → kërkim → burime → verifikim → përfundim. Çdo rresht
// me burim është i klikueshëm dhe hap të njëjtin modal korpusi si badge-t e
// citimeve (CitationSourceModal), kështu që "pse" ka gjurmë deri te teksti.
//
// Pa ndryshime në backend: burimet vijnë nga citations + citation_check që
// stream-i i asistencës tashmë i dërgon; asnjë migrim DB.
import { useState } from "react";

import { useI18n } from "@/lib/i18n";

import type { CitationCheck } from "./citation-checks";

export type TraceKind = "question" | "retrieval" | "source" | "verification" | "answer";

export interface TraceStep {
  kind: TraceKind;
  title: string;
  detail?: string;
  /** Kur ekziston, rreshti hap burimin në korpus (doc/chunk). */
  check?: CitationCheck;
}

export interface TraceInput {
  question?: string;
  queries?: string[];
  citations: { type: string; title: string; section?: string; reference?: string }[];
  checks?: CitationCheck[];
}

const ICON: Record<TraceKind, string> = {
  question: "?",
  retrieval: "⌕",
  source: "▤",
  verification: "✓",
  answer: "→",
};

const STATUS: Record<CitationCheck["status"], string> = {
  verified: "verifikuar",
  approx: "i përafërt",
  law_found: "ligji u gjet",
  unverified: "i paverifikuar",
};

const STATUS_EN: Record<CitationCheck["status"], string> = {
  verified: "verified",
  approx: "approximate",
  law_found: "law found",
  unverified: "unverified",
};

export function buildReasoningTrace(input: TraceInput, lang: "sq" | "en" = "sq"): TraceStep[] {
  const sq = lang !== "en";
  const steps: TraceStep[] = [];
  if (input.question) {
    steps.push({ kind: "question", title: sq ? "Pyetja" : "Question", detail: input.question });
  }
  if (input.queries && input.queries.length) {
    for (const q of input.queries) {
      steps.push({ kind: "retrieval", title: sq ? "Kërkim në korpus" : "Corpus search", detail: q });
    }
  } else {
    steps.push({
      kind: "retrieval",
      title: sq ? "Kërkim në korpus" : "Corpus search",
      detail: sq ? "kërkim semantik mbi burimet e indeksuara" : "semantic search over indexed sources",
    });
  }
  for (const c of input.citations || []) {
    steps.push({
      kind: "source",
      title: c.title,
      detail: [c.section, c.reference].filter(Boolean).join(" · ") || undefined,
    });
  }
  for (const c of input.checks || []) {
    steps.push({
      kind: "verification",
      title: c.cite + " — " + (sq ? STATUS : STATUS_EN)[c.status],
      detail: c.note || c.source_title || undefined,
      check: c,
    });
  }
  const total = input.checks ? input.checks.length : 0;
  const verified = input.checks ? input.checks.filter((c) => c.status === "verified").length : 0;
  steps.push({
    kind: "answer",
    title: sq ? "Përfundim" : "Answer",
    detail: total
      ? (sq ? verified + "/" + total + " citime të verifikuara" : verified + "/" + total + " citations verified")
      : (sq ? "pa citime për verifikim" : "no citations to verify"),
  });
  return steps;
}

export default function ReasoningTrace({
  steps,
  onOpenSource,
}: {
  steps: TraceStep[];
  onOpenSource?: (c: CitationCheck) => void;
}) {
  const { locale } = useI18n();
  const sq = locale !== "en";
  const [open, setOpen] = useState(false);
  if (!steps.length) return null;

  const sources = steps.filter((s) => s.kind === "source").length;
  const checks = steps.filter((s) => s.kind === "verification");
  const verified = checks.filter((s) => s.check?.status === "verified").length;

  return (
    <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 text-xs">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex flex-wrap items-center gap-x-2 gap-y-1 px-3 py-2 text-left"
        aria-expanded={open}
      >
        <span aria-hidden>🧭</span>
        <span className="font-semibold text-indigo-800">
          {sq ? "Gjurmë arsyetimi" : "Reasoning trace"}
        </span>
        <span className="text-slate-500">
          {sq ? steps.length + " hapa" : steps.length + " steps"}
          {sources ? " · " + sources + (sq ? " burime" : " sources") : ""}
          {checks.length ? " · " + verified + "/" + checks.length + (sq ? " të verifikuara" : " verified") : ""}
        </span>
        <span className="ml-auto text-indigo-700">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <ol className="px-3 pb-3 space-y-1">
          {steps.map((s, i) => {
            const clickable = Boolean(s.check?.doc_id && onOpenSource);
            const inner = (
              <>
                <span className="inline-flex w-5 h-5 shrink-0 items-center justify-center rounded-full bg-white border border-indigo-200 text-[10px] text-indigo-700">
                  {ICON[s.kind]}
                </span>
                <span className="font-medium text-slate-800">{s.title}</span>
                {s.detail && <span className="text-slate-500"> — {s.detail}</span>}
                {clickable && (
                  <span className="text-indigo-600 underline decoration-dotted">
                    {" (" + (sq ? "hape burimin" : "open source") + ")"}
                  </span>
                )}
              </>
            );
            return (
              <li key={i} className="flex items-start gap-2">
                {clickable ? (
                  <button
                    type="button"
                    onClick={() => onOpenSource?.(s.check as CitationCheck)}
                    className="flex items-start gap-2 text-left rounded-lg px-1 py-0.5 hover:bg-white/70"
                    title={sq ? "Hap fragmentin e burimit" : "Open the source fragment"}
                  >
                    {inner}
                  </button>
                ) : (
                  <span className="flex items-start gap-2 px-1 py-0.5">{inner}</span>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
