"use client";

/**
 * Umbrella landing: presents the WHOLE project (both sides), then splits the
 * audience immediately — citizens -> /per-qytetaret, lawyers -> /per-avokatet
 * (the "I'm hiring / I'm looking for a job" two-surface pattern).
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import { getToken, setToken } from "@/lib/api";
import { clientCountry, type Country } from "@/lib/country";
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
  judgments_in_corpus: number;
  notaries_licensed: number;
}

export default function Home() {
  const { t } = useI18n();
  // null = not signed in; "lawyer" | "admin" pick the banner wording/target
  const [staffRole, setStaffRole] = useState<"lawyer" | "admin" | null>(null);
  const [stats, setStats] = useState<PublicStats | null>(null);
  // Germany host: no SOS/notary pillar in v1, 3 UI languages (D-034)
  const [country, setCountry] = useState<Country>("XK");
  useEffect(() => setCountry(clientCountry()), []);
  const isDE = country === "DE";

  useEffect(() => {
    // The landing always renders — even for a signed-in lawyer/administrator
    // (they get a "continue" banner instead of an auto-redirect, so the
    // public presentation stays visible). Stale tokens are cleared here
    // (plain fetch: apiGet would hard-redirect to /login on 401).
    // Citizen tokens are recognized by the PublicShell header, not here.
    const token = getToken();
    if (!token) return;
    fetch("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then(async (res) => {
        if (res.ok) {
          const me = (await res.json()) as { is_superadmin?: boolean };
          setStaffRole(me.is_superadmin ? "admin" : "lawyer");
        } else {
          setToken(null);
        }
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
      {/* Signed-in lawyer/administrator: one-click path back, no auto-redirect */}
      {staffRole && (
        <div className={staffRole === "admin" ? "bg-slate-900 text-white" : "bg-indigo-700 text-white"}>
          <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center justify-between gap-3 text-sm">
            <span className="truncate">
              {staffRole === "admin" ? t.umbLoggedAdmin : t.umbLoggedLawyer}
            </span>
            <Link
              href={staffRole === "admin" ? "/platform" : "/dashboard"}
              className="shrink-0 inline-flex items-center gap-1.5 font-semibold bg-white/15 hover:bg-white/25 rounded-lg px-3 py-1.5 transition"
            >
              {staffRole === "admin" ? t.umbGoPlatform : t.umbGoDash}
              <IconArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Hero: the whole project in one breath, then the audience split */}
      <section className="hero-backdrop bg-white border-b border-slate-100 overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 pt-14 pb-14 md:pt-24 md:pb-20 space-y-12">
          <div className="max-w-3xl mx-auto text-center space-y-5">
            <div className="fade-in-up inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white/80 backdrop-blur px-4 py-1.5 shadow-sm">
              <IconScale className="h-4 w-4 text-indigo-600" />
              <span className="text-xs font-semibold tracking-wide text-indigo-700">
                Avokat<span className="text-slate-900">IM</span> · {isDE ? "Deutschland" : "Kosovë"}
              </span>
            </div>
            <h1 className="fade-in-up text-4xl md:text-6xl font-extrabold tracking-tight leading-[1.08] text-hero-gradient bg-clip-text text-transparent pb-1">
              {t.umbHeroT}
            </h1>
            <p className="fade-in-up-d1 text-slate-600 md:text-lg leading-relaxed max-w-2xl mx-auto">
              {t.umbHeroSub}
            </p>
            <div className="fade-in-up-d1 flex flex-wrap items-center justify-center gap-2 pt-1">
              {[
                { Icon: IconCheck, label: t.landTrust1 },
                // Every locale writes the language count as the digit 6;
                // the German host serves 3 UI languages (de/en/tr)
                { Icon: IconGlobe, label: isDE ? t.landTrust2.replace("6", "3") : t.landTrust2 },
                { Icon: IconLock, label: t.landTrust3 },
              ].map(({ Icon, label }) => (
                <span
                  key={label}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/80 backdrop-blur border border-slate-200 px-3 py-1 text-xs text-slate-600 shadow-sm"
                >
                  <Icon className="h-3.5 w-3.5 text-emerald-600" />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* The two doors */}
          <div className="fade-in-up-d2 grid md:grid-cols-2 gap-5 max-w-4xl mx-auto">
            <Link
              href="/per-qytetaret"
              className="group relative bg-white/90 backdrop-blur rounded-3xl ring-1 ring-slate-200 p-7 md:p-8 shadow-sm hover:shadow-xl hover:shadow-indigo-100 hover:ring-indigo-300 hover:-translate-y-1 transition-all duration-300 flex flex-col gap-3.5 overflow-hidden"
            >
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-indigo-500 via-violet-500 to-emerald-400" />
              <div className="rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50 ring-1 ring-indigo-100 text-indigo-600 p-3.5 w-fit group-hover:scale-105 transition-transform">
                <IconChat className="h-8 w-8" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-slate-900">{t.umbCitizenT}</h2>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">{t.umbCitizenB}</p>
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-indigo-700 group-hover:gap-3 transition-all">
                {t.umbCitizenCta}
                <IconArrowRight className="h-4 w-4" />
              </span>
            </Link>
            <Link
              href="/per-avokatet"
              className="group relative bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 rounded-3xl ring-1 ring-slate-700 p-7 md:p-8 shadow-sm hover:shadow-xl hover:shadow-slate-300 hover:ring-indigo-500 hover:-translate-y-1 transition-all duration-300 flex flex-col gap-3.5 overflow-hidden"
            >
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-indigo-400 to-violet-500" />
              <div className="rounded-2xl bg-indigo-500/15 ring-1 ring-indigo-400/30 text-indigo-300 p-3.5 w-fit group-hover:scale-105 transition-transform">
                <IconScale className="h-8 w-8" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-white">{t.umbLawyerT}</h2>
              <p className="text-sm text-slate-300 leading-relaxed flex-1">{t.umbLawyerB}</p>
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-indigo-300 group-hover:gap-3 transition-all">
                {t.umbLawyerCta}
                <IconArrowRight className="h-4 w-4" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      <main className="w-full max-w-5xl mx-auto px-4 py-14 md:py-20 space-y-20">
        {/* What the system does — the full function list, side by side */}
        <section className="space-y-8">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 text-center">
            {t.umbFnT}
          </h2>
          <div className="grid md:grid-cols-2 gap-5">
            <div className="bg-white rounded-3xl ring-1 ring-slate-200 shadow-sm p-6 md:p-8 space-y-4">
              <div className="flex items-center gap-3">
                <span className="rounded-xl bg-emerald-50 ring-1 ring-emerald-100 p-2">
                  <IconUsers className="h-6 w-6 text-emerald-600" />
                </span>
                <h3 className="text-lg font-bold text-slate-900">{t.umbFnCitT}</h3>
              </div>
              <ul className="space-y-2.5 text-sm text-slate-600">
                {(isDE
                  ? [t.umbFnC1.replace("6", "3"), t.umbFnC2, t.umbFnC4, t.umbFnC5, t.umbFnC6, t.umbFnC7, t.umbFnC9]
                  : [t.umbFnC1, t.umbFnC2, t.umbFnC3, t.umbFnC4, t.umbFnC8, t.umbFnC5, t.umbFnC6, t.umbFnC7, t.umbFnC9]
                ).map(
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
                className="inline-flex items-center gap-1.5 py-2 text-sm font-semibold text-indigo-700 hover:text-indigo-900"
              >
                {t.umbCitizenCta}
                <IconArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 rounded-3xl ring-1 ring-slate-700 shadow-sm p-6 md:p-8 space-y-4">
              <div className="flex items-center gap-3">
                <span className="rounded-xl bg-indigo-500/15 ring-1 ring-indigo-400/30 p-2">
                  <IconScale className="h-6 w-6 text-indigo-300" />
                </span>
                <h3 className="text-lg font-bold text-white">{t.umbFnLawT}</h3>
              </div>
              <ul className="space-y-2.5 text-sm text-slate-300">
                {[t.umbFnL1, t.umbFnL2, t.umbFnL7, t.umbFnL3, t.umbFnL4, t.umbFnL5, t.umbFnL8, t.umbFnL6].map((f) => (
                  <li key={f} className="flex items-start gap-2.5">
                    <IconCheck className="h-4 w-4 text-indigo-400 mt-0.5 shrink-0" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href="/per-avokatet"
                className="inline-flex items-center gap-1.5 py-2 text-sm font-semibold text-indigo-300 hover:text-indigo-200"
              >
                {t.umbLawyerCta}
                <IconArrowRight className="h-4 w-4" />
              </Link>
              {/* Second paying profession (Kosovo-only): the notary's office */}
              {!isDE && (
                <Link
                  href="/per-noteret"
                  className="block text-xs text-violet-300/90 hover:text-violet-200 underline underline-offset-2"
                >
                  {t.umbFnL9}
                </Link>
              )}
            </div>
          </div>
        </section>

        {/* Why AvokatIM — the advantages */}
        <section className="space-y-8">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 text-center">
            {t.umbWhyT}
          </h2>
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
                className="bg-white rounded-2xl ring-1 ring-slate-200 p-5 flex items-start gap-3.5 hover:ring-indigo-200 hover:shadow-md hover:shadow-indigo-50 transition-all duration-300"
              >
                <span className="rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50 ring-1 ring-indigo-100 text-indigo-600 p-2 shrink-0">
                  <Icon className="h-5 w-5" />
                </span>
                <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Public stats — lawyers and notaries side by side (owner's call:
            show the real directory count even while it is small) */}
        {stats && (
          <div className={`grid grid-cols-2 ${isDE ? "md:grid-cols-4" : "md:grid-cols-5"} gap-4 text-center max-w-4xl mx-auto`}>
            {[
              { value: stats.laws_in_corpus, label: t.mkStatsLaws },
              // Published case law joined the corpus with D-042 (DE) / D-050 (XK)
              ...(stats.judgments_in_corpus
                ? [{ value: stats.judgments_in_corpus, label: t.mkStatsJudgments }]
                : []),
              { value: stats.lawyers_in_directory, label: t.mkStatsLawyers },
              ...(isDE ? [] : [{ value: stats.notaries_licensed, label: t.mkStatsNotaries }]),
              { value: isDE ? 3 : 6, label: t.mkStatsLangs },
            ].map((s) => (
              <div
                key={s.label}
                className="bg-white rounded-2xl ring-1 ring-slate-200 p-5 hover:ring-indigo-200 transition"
              >
                <p className="text-3xl font-extrabold tracking-tight bg-gradient-to-br from-indigo-700 to-violet-600 bg-clip-text text-transparent">
                  {s.value}
                </p>
                <p className="text-xs text-slate-500 mt-1.5">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Trust & privacy */}
        <section className="max-w-3xl mx-auto bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 rounded-3xl ring-1 ring-slate-700 p-6 md:p-9 text-slate-200">
          <div className="flex items-center gap-3 mb-5">
            <span className="rounded-xl bg-indigo-500/15 ring-1 ring-indigo-400/30 p-2">
              <IconLock className="h-6 w-6 text-indigo-300" />
            </span>
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
          <Link
            href="/siguria"
            className="mt-5 inline-flex items-center gap-1.5 py-2 text-sm font-semibold text-indigo-300 hover:text-indigo-200"
          >
            {t.landPrivLink}
            <IconArrowRight className="h-4 w-4" />
          </Link>
        </section>
      </main>
    </PublicShell>
  );
}
