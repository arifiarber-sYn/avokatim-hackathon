"use client";

/** Marketing page for the supply side: what lawyers get and the plans.
 * Linked discreetly from the citizen-first landing (Avvo/Booking pattern). */
import Link from "next/link";
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";

interface PublicStats {
  cases_posted: number;
  laws_in_corpus: number;
}

export default function ForLawyersPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState<PublicStats | null>(null);

  useEffect(() => {
    fetch("/api/public/stats")
      .then((res) => res.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  const features = [
    t.lpFeat1, t.lpFeat2, t.lpFeat3, t.lpFeat4,
    t.lpFeat5, t.lpFeat6, t.lpFeat7, t.lpFeat8,
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      <header className="border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-indigo-400">
            Avokat<span className="text-white">IM</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-slate-300 hover:text-white">
              {t.login}
            </Link>
            <LocaleSwitcher />
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-14 space-y-12">
        <div className="text-center space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-400">
            {t.mkForLawyersLink}
          </p>
          <h1 className="text-3xl md:text-4xl font-bold text-white">{t.lpTitle}</h1>
          <p className="text-slate-400 max-w-2xl mx-auto">{t.lpSubtitle}</p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/regjistrohu"
              className="rounded-lg bg-indigo-600 text-white px-6 py-3 text-sm font-semibold hover:bg-indigo-500"
            >
              {t.lpCta}
            </Link>
            <Link
              href="/login"
              className="rounded-lg border border-slate-700 text-slate-200 px-6 py-3 text-sm font-medium hover:bg-slate-800"
            >
              {t.login}
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {features.map((f, i) => (
            <div key={i} className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-5 flex gap-3">
              <span className="shrink-0 h-6 w-6 rounded-full bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xs font-bold">
                {i + 1}
              </span>
              <p className="text-sm text-slate-300">{f}</p>
            </div>
          ))}
        </div>

        {/* How the marketplace works for the lawyer */}
        <div className="max-w-3xl mx-auto space-y-4">
          <h2 className="text-xl font-bold text-white text-center">{t.lpHiwT}</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {[t.lpHiw1, t.lpHiw2, t.lpHiw3].map((step, i) => (
              <div key={i} className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-5 space-y-2">
                <span className="inline-flex h-7 w-7 rounded-full bg-indigo-600 text-white items-center justify-center text-xs font-bold">
                  {i + 1}
                </span>
                <p className="text-sm text-slate-300 leading-relaxed">{step}</p>
              </div>
            ))}
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-2 gap-4 max-w-xl mx-auto text-center">
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-4">
              <p className="text-2xl font-bold text-indigo-400">{stats.cases_posted}</p>
              <p className="text-xs text-slate-400 mt-1">{t.mkStatsCases}</p>
            </div>
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-4">
              <p className="text-2xl font-bold text-indigo-400">{stats.laws_in_corpus}</p>
              <p className="text-xs text-slate-400 mt-1">{t.mkStatsLaws}</p>
            </div>
          </div>
        )}

        <div className="max-w-2xl mx-auto space-y-4">
          <h2 className="text-xl font-bold text-white text-center">{t.lpPlansTitle}</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-5">
              <p className="text-sm text-slate-300">{t.lpPlanTrial}</p>
            </div>
            <div className="bg-indigo-600/10 rounded-xl border border-indigo-500/40 p-5">
              <p className="text-sm text-slate-200">{t.lpPlanPaid}</p>
            </div>
          </div>
          <div className="text-center pt-2">
            <Link
              href="/regjistrohu"
              className="inline-block rounded-lg bg-indigo-600 text-white px-6 py-3 text-sm font-semibold hover:bg-indigo-500"
            >
              {t.lpCta}
            </Link>
          </div>
        </div>

        <footer className="text-center text-xs text-slate-500 space-x-4 border-t border-slate-800 pt-6">
          <Link href="/" className="hover:underline">AvokatIM</Link>
          <Link href="/portal" className="hover:underline">{t.portalTitle}</Link>
          <Link href="/kushtet" className="hover:underline">{t.termsOfService}</Link>
          <Link href="/privatesia" className="hover:underline">{t.privacyPolicy}</Link>
          <Link href="/kontakti" className="hover:underline">{t.ctTitle}</Link>
        </footer>
      </main>
    </div>
  );
}
