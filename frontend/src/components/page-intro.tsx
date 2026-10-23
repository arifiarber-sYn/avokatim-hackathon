"use client";

/**
 * Dismissible per-page explainer ("how this page works"). Shown expanded on
 * first visit; once dismissed it collapses into a small "?" pill that brings
 * it back. Dismissal is remembered per page in localStorage.
 */
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";

function InfoIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" strokeLinecap="round" />
      <circle cx="12" cy="8" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

export default function PageIntro({
  k,
  title,
  body,
}: {
  k: string;
  title: string;
  body: string;
}) {
  const { t } = useI18n();
  // null until localStorage is read — render nothing to avoid hydration flash
  const [open, setOpen] = useState<boolean | null>(null);
  const storageKey = `avokatim:intro:${k}`;

  useEffect(() => {
    try {
      setOpen(localStorage.getItem(storageKey) !== "1");
    } catch {
      setOpen(true);
    }
  }, [storageKey]);

  function dismiss() {
    setOpen(false);
    try {
      localStorage.setItem(storageKey, "1");
    } catch {}
  }

  function reopen() {
    setOpen(true);
    try {
      localStorage.removeItem(storageKey);
    } catch {}
  }

  if (open === null) return null;

  if (!open) {
    return (
      <button
        type="button"
        onClick={reopen}
        className="inline-flex items-center gap-1.5 py-1.5 text-xs text-slate-400 hover:text-indigo-600 transition"
      >
        <InfoIcon className="h-3.5 w-3.5" />
        {t.introShow}
      </button>
    );
  }

  return (
    <div className="relative rounded-xl border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-white p-4 sm:p-5">
      <div className="flex gap-3">
        <div className="shrink-0 h-8 w-8 rounded-full bg-indigo-600 text-white flex items-center justify-center">
          <InfoIcon className="h-4 w-4" />
        </div>
        <div className="min-w-0 space-y-1">
          <p className="font-semibold text-slate-900 text-sm">{title}</p>
          <p className="text-sm text-slate-600 leading-relaxed">{body}</p>
          <button
            type="button"
            onClick={dismiss}
            className="mt-1 py-1.5 text-xs font-semibold text-indigo-700 hover:text-indigo-900"
          >
            {t.introHide}
          </button>
        </div>
      </div>
    </div>
  );
}
