"use client";

/**
 * Umbrella landing: presents the WHOLE project (both sides), then splits the
 * audience immediately — citizens -> /per-qytetaret, lawyers -> /per-avokatet
 * (the "I'm hiring / I'm looking for a job" two-surface pattern).
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import { getToken, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import {
  IconArrowRight,
  IconCheck,
  IconChat,
  IconGlobe,
  IconLock,
  IconScale,
  IconShield,
  IconUsers,
} from "@/components/icons";

interface PublicStats {
  lawyers_in_directory: number;
  cases_posted: number;
  cases_taken: number;
  laws_in_corpus: number;
}

export default function Home() {
  const { t } = useI18n();
  const [lawyerLogged, setLawyerLogged] = useState(false);
  const [stats, setStats] = useState<PublicStats | null>(null);

  useEffect(() => {
    // The landing always renders — even for a signed-in lawyer (they get a
    // "continue to dashboard" banner instead of an auto-redirect, so the
    // public presentation stays visible). Stale tokens are cleared here
    // (plain fetch: apiGet would hard-redirect to /login on 401).
    // Citizen tokens are recognized by the PublicShell header, not here.
    const token = getToken();
    if (!token) return;
    fetch("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (res.ok) setLawyerLogged(true);
        else setToken(null);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch("/api/public/stats")
      .then((res) => res.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  return (
    <PublicShell wide>
      {/* Signed-in lawyer: one-click path back to work, no auto-redirect */}
      {lawyerLogged && (
        <div className="bg-indigo-700 text-white">
          <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center justify-between gap-3 text-sm">
            <span className="truncate">{t.umbLoggedLawyer}</span>
            <Link
              href="/dashboard"
              className="shrink-0 inline-flex items-center gap-1.5 font-semibold bg-white/15 hover:bg-white/25 rounded-lg px-3 py-1.5 transition"
            >
              {t.umbGoDash}
              <IconArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Hero: the whole project in one breath, then the audience split */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-white to-slate-50 border-b border-slate-100">
        <div className="max-w-5xl mx-auto px-4 pt-12 pb-12 md:pt-20 md:pb-16 space-y-10">
          <div className="max-w-3xl mx-auto text-center space-y-4 fade-in-up">
            <h1 className="text-3xl md:text-5xl font-bold text-slate-900 tracking-tight">
              {t.umbHeroT}
            </h1>
            <p className="text-slate-600 md:text-lg leading-relaxed">{t.umbHeroSub}</p>
            <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5 text-xs text-slate-500 pt-1">
              {[
                { Icon: IconCheck, label: t.landTrust1 },
                { Icon: IconGlobe, label: t.landTrust2 },
                { Icon: IconLock, label: t.landTrust3 },
              ].map(({ Icon, label }) => (
                <span key={label} className="inline-flex items-center gap-1.5">
                  <Icon className="h-3.5 w-3.5 text-emerald-600" />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* The two doors */}
          <div className="grid md:grid-cols-2 gap-5 max-w-4xl mx-auto">
            <Link
              href="/per-qytetaret"
              className="group bg-white rounded-2xl border-2 border-indigo-200 p-7 shadow-sm hover:shadow-md hover:border-indigo-400 transition flex flex-col gap-3"
            >
              <div className="rounded-2xl bg-indigo-50 text-indigo-600 p-3.5 w-fit">
                <IconChat className="h-8 w-8" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-slate-900">{t.umbCitizenT}</h2>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">{t.umbCitizenB}</p>
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-indigo-700 group-hover:gap-2.5 transition-all">
                {t.umbCitizenCta}
                <IconArrowRight className="h-4 w-4" />
              </span>
            </Link>
            <Link
              href="/per-avokatet"
              className="group bg-slate-900 rounded-2xl border-2 border-slate-700 p-7 shadow-sm hover:shadow-md hover:border-indigo-500 transition flex flex-col gap-3"
            >
              <div className="rounded-2xl bg-indigo-500/20 text-indigo-300 p-3.5 w-fit">
                <IconScale className="h-8 w-8" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-white">{t.umbLawyerT}</h2>
              <p className="text-sm text-slate-300 leading-relaxed flex-1">{t.umbLawyerB}</p>
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-indigo-300 group-hover:gap-2.5 transition-all">
                {t.umbLawyerCta}
                <IconArrowRight className="h-4 w-4" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      <main className="w-full max-w-5xl mx-auto px-4 py-12 space-y-16">
        {/* What the system does — the full function list, side by side */}
        <section className="space-y-6">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 text-center">{t.umbFnT}</h2>
          <div className="grid md:grid-cols-2 gap-5">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 md:p-7 space-y-4">
              <div className="flex items-center gap-2.5">
                <IconUsers className="h-6 w-6 text-emerald-600" />
                <h3 className="text-lg font-bold text-slate-900">{t.umbFnCitT}</h3>
              </div>
              <ul className="space-y-2.5 text-sm text-slate-600">
                {[t.umbFnC1, t.umbFnC2, t.umbFnC3, t.umbFnC4, t.umbFnC5, t.umbFnC6, t.umbFnC7].map(
                  (f) => (
                    <li key={f} className="flex items-start gap-2.5">
                      <IconCheck className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                      <span>{f}</span>
                    </li>
                  )
                )}
              </ul>
              <Link
                href="/per-qytetaret"
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-700 hover:text-indigo-900"
              >
                {t.umbCitizenCta}
                <IconArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="bg-slate-900 rounded-2xl p-6 md:p-7 space-y-4">
              <div className="flex items-center gap-2.5">
                <IconScale className="h-6 w-6 text-indigo-400" />
                <h3 className="text-lg font-bold text-white">{t.umbFnLawT}</h3>
              </div>
              <ul className="space-y-2.5 text-sm text-slate-300">
                {[t.umbFnL1, t.umbFnL2, t.umbFnL3, t.umbFnL4, t.umbFnL5, t.umbFnL6].map((f) => (
                  <li key={f} className="flex items-start gap-2.5">
                    <IconCheck className="h-4 w-4 text-indigo-400 mt-0.5 shrink-0" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href="/per-avokatet"
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-300 hover:text-indigo-200"
              >
                {t.umbLawyerCta}
                <IconArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Why AvokatIM — the advantages */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold text-slate-900 text-center">{t.umbWhyT}</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { Icon: IconGlobe, text: t.umbWhy1 },
              { Icon: IconChat, text: t.umbWhy2 },
              { Icon: IconLock, text: t.umbWhy3 },
              { Icon: IconCheck, text: t.umbWhy4 },
              { Icon: IconShield, text: t.umbWhy5 },
            ].map(({ Icon, text }) => (
              <div
                key={text}
                className="bg-white rounded-xl border border-slate-200 p-5 flex items-start gap-3"
              >
                <span className="rounded-lg bg-indigo-50 text-indigo-600 p-2 shrink-0">
                  <Icon className="h-5 w-5" />
                </span>
                <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Public stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center max-w-3xl mx-auto">
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

        {/* Trust & privacy */}
        <section className="max-w-3xl mx-auto bg-slate-900 rounded-2xl p-6 md:p-8 text-slate-200">
          <div className="flex items-center gap-3 mb-4">
            <IconLock className="h-6 w-6 text-indigo-400" />
            <h2 className="text-xl font-bold text-white">{t.landPrivT}</h2>
          </div>
          <ul className="grid sm:grid-cols-2 gap-3 text-sm">
            {[t.landPriv1, t.landPriv2, t.landPriv3, t.landPriv4].map((p) => (
              <li key={p} className="flex items-start gap-2">
                <IconCheck className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </PublicShell>
  );
}
