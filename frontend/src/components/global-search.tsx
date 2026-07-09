"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

interface SearchResults {
  matters: { id: string; reference: string; title: string; status: string }[];
  contacts: { id: string; display_name: string; email: string | null; kind: string }[];
  documents: { id: string; matter_id: string | null; filename: string; snippet: string | null }[];
  invoices: { id: string; number: string; status: string; matter_id: string | null }[];
}

export function GlobalSearch({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (q.trim().length < 2) {
      setResults(null);
      return;
    }
    const timer = setTimeout(async () => {
      setBusy(true);
      try {
        const r = await apiGet<SearchResults>(`/search?q=${encodeURIComponent(q.trim())}`);
        setResults(r);
        setOpen(true);
      } catch {
        setResults(null);
      } finally {
        setBusy(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [q]);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const empty =
    results &&
    results.matters.length === 0 &&
    results.contacts.length === 0 &&
    results.documents.length === 0 &&
    results.invoices.length === 0;

  function close() {
    setOpen(false);
    setQ("");
    onNavigate?.();
  }

  function group(label: string, items: React.ReactNode[]) {
    if (items.length === 0) return null;
    return (
      <div>
        <p className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
          {label}
        </p>
        {items}
      </div>
    );
  }

  return (
    <div ref={boxRef} className="relative w-full max-w-md">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => results && setOpen(true)}
        placeholder={`⌕ ${t.searchEverything}`}
        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      {open && (results || busy) && (
        <div className="absolute z-50 mt-1 w-full max-h-[28rem] overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-xl divide-y divide-slate-100 pb-1">
          {busy && !results && (
            <p className="px-3 py-3 text-sm text-slate-400">{t.loading}</p>
          )}
          {empty && <p className="px-3 py-3 text-sm text-slate-400">{t.noResults}</p>}
          {results &&
            group(
              t.matters,
              results.matters.map((m) => (
                <Link
                  key={m.id}
                  href={`/matters/${m.id}`}
                  onClick={close}
                  className="block px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  <span className="font-mono text-xs text-slate-500 mr-2">{m.reference}</span>
                  {m.title}
                </Link>
              ))
            )}
          {results &&
            group(
              t.contacts,
              results.contacts.map((c) => (
                <Link
                  key={c.id}
                  href="/contacts"
                  onClick={close}
                  className="block px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  {c.display_name}
                  {c.email && <span className="text-xs text-slate-400 ml-2">{c.email}</span>}
                </Link>
              ))
            )}
          {results &&
            group(
              t.documents,
              results.documents.map((d) => (
                <Link
                  key={d.id}
                  href={d.matter_id ? `/matters/${d.matter_id}` : "/matters"}
                  onClick={close}
                  className="block px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  <span className="truncate block">{d.filename}</span>
                  {d.snippet && (
                    <span className="text-xs text-slate-400 truncate block">{d.snippet}</span>
                  )}
                </Link>
              ))
            )}
          {results &&
            group(
              t.invoices,
              results.invoices.map((i) => (
                <Link
                  key={i.id}
                  href="/billing"
                  onClick={close}
                  className="block px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  <span className="font-mono">{i.number}</span>
                  <span className="text-xs text-slate-400 ml-2">{i.status}</span>
                </Link>
              ))
            )}
        </div>
      )}
    </div>
  );
}
