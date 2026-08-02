"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

/** Forgiving subsequence match ("nlnd" finds "Lëndë e re") for the
 * command-palette actions (D-054 F5). */
function fuzzy(needle: string, haystack: string): boolean {
  const n = needle.toLowerCase();
  const h = haystack.toLowerCase();
  let i = 0;
  for (const ch of h) {
    if (ch === n[i]) i++;
    if (i === n.length) return true;
  }
  return i === n.length;
}

interface SearchResults {
  matters: { id: string; reference: string; title: string; status: string }[];
  contacts: { id: string; display_name: string; email: string | null; kind: string }[];
  documents: { id: string; matter_id: string | null; filename: string; snippet: string | null }[];
  invoices: { id: string; number: string; status: string; matter_id: string | null }[];
  deadlines: { id: string; matter_id: string; matter_reference: string; title: string; due_at: string | null; status: string }[];
  tasks: { id: string; matter_id: string | null; title: string; status: string }[];
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

  // Cmd+K / Ctrl+K focuses the search from anywhere in the app (D-053)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        boxRef.current?.querySelector("input")?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // "Ask Ava" row: hands the query to the assistant panel (D-053)
  function askAva() {
    const question = q.trim();
    setOpen(false);
    setQ("");
    window.dispatchEvent(
      new CustomEvent("avokatim:ask-ava", { detail: { question } })
    );
  }

  // Command palette (D-054 F5): quick actions and destinations, fuzzy-matched
  const actions = useMemo(
    () => [
      { label: t.newMatter, href: "/matters?new=1", icon: "＋" },
      { label: t.addDeadline, href: "/calendar", icon: "＋" },
      { label: t.newInvoice, href: "/billing", icon: "＋" },
      { label: t.newContact, href: "/contacts", icon: "＋" },
      { label: t.dashboard, href: "/dashboard", icon: "▦" },
      { label: t.matters, href: "/matters", icon: "▤" },
      { label: t.calendar, href: "/calendar", icon: "▧" },
      { label: t.assistant, href: "/assistant", icon: "✦" },
      { label: t.analytics, href: "/reports", icon: "◫" },
      { label: t.settings, href: "/settings", icon: "⚙" },
    ],
    [t]
  );
  const matchedActions = q.trim()
    ? actions.filter((a) => fuzzy(q.trim(), a.label)).slice(0, 5)
    : actions.slice(0, 6);

  const empty =
    results &&
    results.matters.length === 0 &&
    results.contacts.length === 0 &&
    results.documents.length === 0 &&
    results.invoices.length === 0 &&
    (results.deadlines?.length ?? 0) === 0 &&
    (results.tasks?.length ?? 0) === 0;

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
        onFocus={() => setOpen(true)}
        placeholder={`⌕ ${t.searchEverything}`}
        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      {open && (results || busy || matchedActions.length > 0) && (
        <div className="absolute z-50 mt-1 w-full max-h-[28rem] overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-xl divide-y divide-slate-100 pb-1">
          {q.trim().length >= 2 && (
            <button
              onClick={askAva}
              className="w-full text-left px-3 py-2 text-sm text-indigo-700 hover:bg-indigo-50 font-medium flex items-center gap-2"
            >
              <span className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-xs shrink-0">✦</span>
              <span className="truncate">{t.gsAskAva.replace("{q}", q.trim())}</span>
            </button>
          )}
          {group(
            t.gsActions,
            matchedActions.map((a) => (
              <Link
                key={a.href + a.label}
                href={a.href}
                onClick={close}
                className="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                <span className="w-4 text-center text-slate-400">{a.icon}</span>
                {a.label}
              </Link>
            ))
          )}
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
              t.deadlines,
              (results.deadlines || []).map((d) => (
                <Link
                  key={d.id}
                  href={`/matters/${d.matter_id}`}
                  onClick={close}
                  className="block px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  <span className={d.status === "done" ? "line-through text-slate-400" : ""}>{d.title}</span>
                  <span className="text-xs text-slate-400 ml-2">
                    {d.matter_reference}
                    {d.due_at ? ` · ${new Date(d.due_at).toLocaleDateString()}` : ""}
                  </span>
                </Link>
              ))
            )}
          {results &&
            group(
              t.myTasks,
              (results.tasks || []).map((tk) => (
                <Link
                  key={tk.id}
                  href={tk.matter_id ? `/matters/${tk.matter_id}` : "/dashboard"}
                  onClick={close}
                  className="block px-3 py-1.5 text-sm hover:bg-slate-50"
                >
                  <span className={tk.status === "done" ? "line-through text-slate-400" : ""}>{tk.title}</span>
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
