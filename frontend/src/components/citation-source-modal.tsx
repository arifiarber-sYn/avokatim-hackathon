"use client";

// Source view behind a citation badge (audit 2026-09-18, clickable
// citations): fetches the verified corpus chunk and shows it in a modal,
// with a link to the official source when we have one.
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

import type { CitationCheck } from "./citation-checks";

interface ChunkSource {
  chunk_id: string;
  section: string | null;
  text: string;
  doc_id: string;
  doc_title: string;
  doc_reference: string | null;
  doc_type: string;
  source_url: string | null;
  language: string;
}

export default function CitationSourceModal({
  citation,
  onClose,
}: {
  citation: CitationCheck | null;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const [source, setSource] = useState<ChunkSource | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setSource(null);
    setError(false);
    if (!citation?.doc_id) return;
    const path = citation.chunk_id
      ? `/corpus/chunk/${citation.chunk_id}`
      : `/corpus/doc/${citation.doc_id}/first-chunk`;
    apiGet<ChunkSource>(path).then(setSource).catch(() => setError(true));
  }, [citation]);

  if (!citation) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-xl bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">{t.ccSourceTitle}</p>
            <h3 className="text-base font-semibold text-slate-900">{citation.cite}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100"
          >
            {t.close}
          </button>
        </div>
        {error && <p className="mt-4 text-sm text-slate-500">{t.error}</p>}
        {!source && !error && <p className="mt-4 text-sm text-slate-400">…</p>}
        {source && (
          <div className="mt-3 space-y-3">
            <div className="text-sm text-slate-600">
              <span className="font-medium">{source.doc_title}</span>
              {source.doc_reference && (
                <span className="text-slate-400"> · {source.doc_reference}</span>
              )}
              {source.section && (
                <span className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs">
                  {source.section}
                </span>
              )}
            </div>
            <blockquote className="whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm leading-relaxed text-slate-800">
              {source.text}
            </blockquote>
            {source.source_url && (
              <a
                href={source.source_url}
                target="_blank"
                rel="noreferrer"
                className="inline-block text-sm text-blue-600 hover:underline"
              >
                {t.ccSourceOfficial} ↗
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
