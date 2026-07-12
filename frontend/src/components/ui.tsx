"use client";

import { useEffect, useRef, useState } from "react";
import { LOCALES } from "@/lib/dictionaries";
import { useI18n } from "@/lib/i18n";

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
}) {
  const styles = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300",
    secondary:
      "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 disabled:text-slate-400",
    danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
    ghost: "text-slate-600 hover:bg-slate-100",
  };
  return (
    <button
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${props.className || ""}`}
    />
  );
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={`w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${props.className || ""}`}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`w-full px-3 py-2 rounded-lg border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 ${props.className || ""}`}
    />
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-slate-700 mb-1">{children}</label>;
}

const STATUS_COLORS: Record<string, string> = {
  open: "bg-emerald-100 text-emerald-800",
  intake: "bg-amber-100 text-amber-800",
  on_hold: "bg-slate-100 text-slate-600",
  closed: "bg-slate-200 text-slate-700",
  archived: "bg-slate-100 text-slate-500",
  pending: "bg-amber-100 text-amber-800",
  done: "bg-emerald-100 text-emerald-800",
  missed: "bg-red-100 text-red-800",
  new: "bg-blue-100 text-blue-800",
  conflict: "bg-red-100 text-red-800",
  accepted: "bg-emerald-100 text-emerald-800",
  declined: "bg-slate-200 text-slate-600",
  draft: "bg-slate-100 text-slate-600",
  sent: "bg-blue-100 text-blue-800",
  paid: "bg-emerald-100 text-emerald-800",
  void: "bg-slate-200 text-slate-500",
};

export function Badge({ status, label }: { status: string; label?: string }) {
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[status] || "bg-slate-100 text-slate-600"}`}
    >
      {label || status}
    </span>
  );
}

/** Language picker as a compact dropdown (globe + current language) so all
 * six languages fit on any screen — the old inline button row overflowed
 * phone viewports. Menu is right-aligned to stay inside header edges. */
export function LocaleSwitcher({
  up = false,
  iconOnly = false,
}: {
  up?: boolean;
  /** Globe-only trigger for tight headers; the menu still shows full names. */
  iconOnly?: boolean;
}) {
  const { locale, setLocale } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const current = LOCALES.find((l) => l.code === locale);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={current?.label ?? locale}
        className={
          iconOnly
            ? "inline-flex items-center justify-center h-9 w-9 rounded-full text-slate-500 hover:text-indigo-700 hover:bg-slate-100 transition"
            : "inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/90 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-indigo-300 hover:text-indigo-700 transition shadow-sm"
        }
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={iconOnly ? "h-5 w-5" : "h-4 w-4"}>
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18" />
        </svg>
        {!iconOnly && (
          <>
            <span>{current?.label ?? locale}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`}>
              <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </>
        )}
      </button>
      {open && (
        <div
          role="listbox"
          className={`absolute w-40 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 ${
            up ? "left-0 bottom-full mb-2" : "right-0 top-full mt-2"
          }`}
        >
          {LOCALES.map((l) => (
            <button
              key={l.code}
              role="option"
              aria-selected={locale === l.code}
              onClick={() => {
                setLocale(l.code);
                setOpen(false);
              }}
              className={`flex w-full items-center justify-between px-3.5 py-2 text-sm text-left transition ${
                locale === l.code
                  ? "text-indigo-700 font-semibold bg-indigo-50"
                  : "text-slate-700 hover:bg-slate-50"
              }`}
            >
              {l.label}
              {locale === l.code && (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-4 w-4">
                  <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function Spinner() {
  return (
    <div className="flex justify-center py-8">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  if (!message) return null;
  return (
    <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
      {message}
    </div>
  );
}
