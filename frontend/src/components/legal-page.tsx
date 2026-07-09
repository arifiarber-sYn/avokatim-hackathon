"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { LegalDoc } from "@/lib/legal";
import { Locale } from "@/lib/dictionaries";
import { Card, LocaleSwitcher } from "./ui";

export function LegalPage({ docs }: { docs: Record<Locale, LegalDoc> }) {
  const { t, locale } = useI18n();
  const doc = docs[locale] || docs.sq;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between gap-3">
          <Link href="/" className="text-lg font-bold text-indigo-700">
            {t.appName}
          </Link>
          <LocaleSwitcher />
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-4 py-8">
        <Card className="p-6 sm:p-8 space-y-5">
          <div>
            <h1 className="text-xl font-bold">{doc.title}</h1>
            <p className="text-xs text-slate-500 mt-1">{doc.updated}</p>
            {locale !== "sq" && <p className="text-xs text-slate-400 mt-0.5">{doc.note}</p>}
          </div>
          {doc.sections.map((s, i) => (
            <section key={i}>
              <h2 className="font-semibold text-sm mb-1">
                {i + 1}. {s.h}
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">{s.p}</p>
            </section>
          ))}
          <div className="pt-2 border-t border-slate-100 flex gap-4 text-sm">
            <Link href="/kushtet" className="text-indigo-600 hover:underline">
              {t.termsOfService}
            </Link>
            <Link href="/privatesia" className="text-indigo-600 hover:underline">
              {t.privacyPolicy}
            </Link>
          </div>
        </Card>
      </main>
    </div>
  );
}
