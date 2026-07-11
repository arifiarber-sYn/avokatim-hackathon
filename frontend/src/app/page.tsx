"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";

interface PublicStats {
  lawyers_in_directory: number;
  cases_posted: number;
  cases_taken: number;
  laws_in_corpus: number;
}

export default function Home() {
  const router = useRouter();
  const { t } = useI18n();
  const [ready, setReady] = useState(false);
  const [stats, setStats] = useState<PublicStats | null>(null);

  useEffect(() => {
    // Logged-in lawyers go straight to their dashboard
    if (getToken()) router.replace("/dashboard");
    else setReady(true);
  }, [router]);

  useEffect(() => {
    if (!ready) return;
    fetch("/api/public/stats")
      .then((res) => res.json())
      .then(setStats)
      .catch(() => {});
  }, [ready]);

  if (!ready) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <span className="text-lg font-bold text-indigo-700">
            Avokat<span className="text-slate-900">IM</span>
          </span>
          <LocaleSwitcher />
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-14 space-y-10">
        <div className="text-center space-y-3">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">AvokatIM</h1>
          <p className="text-slate-500">{t.tagline}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 space-y-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
              {t.mkForCitizens}
            </p>
            <h2 className="text-xl font-bold text-slate-900">{t.mkHeroCitizen}</h2>
            <div className="space-y-3">
              <Link
                href="/avokatet"
                className="block w-full text-center rounded-lg bg-indigo-600 text-white py-2.5 text-sm font-medium hover:bg-indigo-700"
              >
                {t.mkFindLawyer}
              </Link>
              <Link
                href="/ava"
                className="block w-full text-center rounded-lg border border-indigo-200 text-indigo-700 py-2.5 text-sm font-medium hover:bg-indigo-50"
              >
                {t.mkAskAva}
              </Link>
              <Link
                href="/posto-rastin"
                className="block w-full text-center rounded-lg border border-indigo-200 text-indigo-700 py-2.5 text-sm font-medium hover:bg-indigo-50"
              >
                {t.mkPostCase}
              </Link>
              <Link
                href="/rasti-im"
                className="block text-center text-sm text-slate-500 hover:underline"
              >
                {t.mkMyCase}
              </Link>
            </div>
            <p className="text-xs text-slate-400">{t.mkDisclaimer}</p>
          </section>

          <section className="bg-slate-900 rounded-2xl shadow-sm p-8 space-y-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-300">
              {t.mkForLawyers}
            </p>
            <h2 className="text-xl font-bold text-white">{t.mkHeroLawyer}</h2>
            <div className="space-y-3">
              <Link
                href="/login"
                className="block w-full text-center rounded-lg bg-white text-slate-900 py-2.5 text-sm font-medium hover:bg-slate-100"
              >
                {t.login}
              </Link>
              <Link
                href="/regjistrohu"
                className="block w-full text-center rounded-lg border border-slate-600 text-slate-200 py-2.5 text-sm font-medium hover:bg-slate-800"
              >
                {t.createAccount}
              </Link>
              <Link
                href="/portal"
                className="block text-center text-sm text-slate-400 hover:underline"
              >
                {t.portalTitle}
              </Link>
            </div>
          </section>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            {[
              { value: stats.lawyers_in_directory, label: t.mkStatsLawyers },
              { value: stats.cases_posted, label: t.mkStatsCases },
              { value: stats.cases_taken, label: t.mkStatsTaken },
              { value: stats.laws_in_corpus, label: t.mkStatsLaws },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl border border-slate-200 p-4">
                <p className="text-2xl font-bold text-indigo-700">{s.value}</p>
                <p className="text-xs text-slate-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        <footer className="text-center text-xs text-slate-400 space-x-4">
          <Link href="/kushtet" className="hover:underline">{t.termsOfService}</Link>
          <Link href="/privatesia" className="hover:underline">{t.privacyPolicy}</Link>
        </footer>
      </main>
    </div>
  );
}
