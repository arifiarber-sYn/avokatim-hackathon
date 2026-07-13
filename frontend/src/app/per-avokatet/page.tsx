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

      <main className="max-w-4xl mx-auto px-4 py-14 md:py-18 space-y-12">
        <div className="text-center space-y-5 fade-in-up">
          <p className="inline-flex items-center rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-indigo-300">
            {t.mkForLawyersLink}
          </p>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1] bg-gradient-to-br from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent pb-1">
            {t.lpTitle}
          </h1>
          <p className="text-slate-400 md:text-lg max-w-2xl mx-auto">{t.lpSubtitle}</p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/regjistrohu"
              className="rounded-xl bg-indigo-600 text-white px-7 py-3 text-sm font-semibold hover:bg-indigo-500 shadow-lg shadow-indigo-950 hover:-translate-y-0.5 transition-all duration-300"
            >
              {t.lpCta}
            </Link>
            <Link
              href="/login"
              className="rounded-xl border border-slate-700 text-slate-200 px-7 py-3 text-sm font-medium hover:bg-slate-800 hover:border-slate-500 transition"
            >
              {t.login}
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {features.map((f, i) => (
            <div
              key={i}
              className="bg-slate-800/60 rounded-2xl border border-slate-700/60 p-5 flex gap-3 hover:border-indigo-500/50 hover:bg-slate-800 transition-colors duration-300"
            >
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

        {/* Early-adopter recruitment: the founder badge */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-gradient-to-br from-amber-500/10 to-indigo-600/10 rounded-xl border border-amber-500/30 p-6 text-center space-y-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-300 bg-amber-500/10 rounded-full px-3 py-1">
              <svg viewBox="0 0 24 24" fill="currentColor" className="h-3.5 w-3.5">
                <path d="M12 2l2.9 6.26L21 9.27l-4.5 4.38L17.8 21 12 17.77 6.2 21l1.3-7.35L3 9.27l6.1-1.01L12 2z" />
              </svg>
              {t.mkFounder}
            </span>
            <h2 className="text-lg font-bold text-white">{t.lpFounderT}</h2>
            <p className="text-sm text-slate-300">{t.lpFounderB}</p>
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
