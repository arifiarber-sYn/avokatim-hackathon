"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getToken, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Textarea } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import {
  IconArrowRight,
  IconCalendar,
  IconChat,
  IconCheck,
  IconDoc,
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
  const router = useRouter();
  const { t } = useI18n();
  const [ready, setReady] = useState(false);
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [question, setQuestion] = useState("");

  useEffect(() => {
    // Lawyers with a VALID session go straight to their dashboard. A stale
    // token must not trap visitors on the login page — validate it first
    // (plain fetch: apiGet would hard-redirect to /login on 401).
    const token = getToken();
    if (!token) {
      setReady(true);
      return;
    }
    fetch("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (res.ok) {
          router.replace("/dashboard");
        } else {
          setToken(null);
          setReady(true);
        }
      })
      .catch(() => setReady(true));
  }, [router]);

  useEffect(() => {
    if (!ready) return;
    fetch("/api/public/stats")
      .then((res) => res.json())
      .then(setStats)
      .catch(() => {});
  }, [ready]);

  function askAva(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (q) localStorage.setItem("avokatim_ava_prefill", q.slice(0, 2000));
    router.push("/ava");
  }

  if (!ready) return null;

  return (
    <PublicShell wide>
      {/* Hero */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-white to-slate-50 border-b border-slate-100">
        <div className="max-w-5xl mx-auto px-4 pt-12 pb-10 md:pt-20 md:pb-14">
          <div className="max-w-2xl mx-auto text-center space-y-4 fade-in-up">
            <h1 className="text-3xl md:text-5xl font-bold text-slate-900 tracking-tight">
              {t.mkHeroTitle}
            </h1>
            <p className="text-slate-500 md:text-lg">{t.mkHeroCitizen}</p>
            <form
              onSubmit={askAva}
              className="bg-white rounded-2xl border border-slate-200 shadow-md p-3 space-y-2 text-left"
            >
              <Textarea
                rows={2}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t.mkAvaPlaceholder}
                className="border-0 focus:ring-0 resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    askAva(e);
                  }
                }}
              />
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-slate-400 hidden sm:block">
                  {t.mkAvaDisclaimer.split(".")[0]}.
                </p>
                <Button type="submit" className="shrink-0">
                  {t.mkAskAva}
                </Button>
              </div>
            </form>
            {/* Trust strip */}
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

          {/* Secondary paths */}
          <div className="grid sm:grid-cols-3 gap-4 max-w-3xl mx-auto mt-10">
            <Link
              href="/avokatet"
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-indigo-300 hover:shadow-sm transition"
            >
              <IconUsers className="h-6 w-6 text-indigo-600 mb-2" />
              <p className="font-semibold text-slate-900">{t.mkFindLawyer}</p>
              <p className="text-xs text-slate-500 mt-1">{t.mkLawyersDirectory}</p>
            </Link>
            <Link
              href="/posto-rastin"
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-indigo-300 hover:shadow-sm transition"
            >
              <IconDoc className="h-6 w-6 text-indigo-600 mb-2" />
              <p className="font-semibold text-slate-900">{t.mkPostCase}</p>
              <p className="text-xs text-slate-500 mt-1">{t.mkHeroCitizen.split("—")[0]}</p>
            </Link>
            <Link href="/rasti-im?sos=1" className="bg-red-600 rounded-xl p-5 hover:bg-red-700 transition">
              <IconShield className="h-6 w-6 text-red-100 mb-2" />
              <p className="font-bold text-white">{t.mkSos}</p>
              <p className="text-xs text-red-100 mt-1">{t.mkSosDutyHint}</p>
            </Link>
          </div>
        </div>
      </section>

      <main className="w-full max-w-5xl mx-auto px-4 py-12 space-y-16">
        {/* What is AvokatIM — the full project description */}
        <section className="max-w-3xl mx-auto text-center space-y-4">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900">{t.landWhatT}</h2>
          <p className="text-slate-600 leading-relaxed">{t.landWhat1}</p>
          <p className="text-slate-600 leading-relaxed">{t.landWhat2}</p>
        </section>

        {/* Four alternating feature sections */}
        <section className="space-y-10">
          {[
            {
              Icon: IconChat,
              tone: "indigo",
              title: t.landAvaT,
              body: t.landAvaB,
              cta: { href: "/ava", label: t.landAvaCta },
              links: undefined,
            },
            {
              Icon: IconShield,
              tone: "red",
              title: t.landSosT,
              body: t.landSosB,
              cta: { href: "/rasti-im?sos=1", label: t.landSosCta },
              links: undefined,
            },
            {
              Icon: IconUsers,
              tone: "emerald",
              title: t.landMarketT,
              body: t.landMarketB,
              cta: { href: "/avokatet", label: t.landMarketCta },
              links: undefined,
            },
            {
              Icon: IconDoc,
              tone: "amber",
              title: t.landToolsT,
              body: t.landToolsB,
              cta: undefined,
              links: [
                { href: "/afatet", label: t.landToolsDeadlines, Icon: IconCalendar },
                { href: "/dokumentet", label: t.landToolsDocs, Icon: IconDoc },
              ],
            },
          ].map((f, i) => {
            const tones: Record<string, string> = {
              indigo: "bg-indigo-50 text-indigo-600",
              red: "bg-red-50 text-red-600",
              emerald: "bg-emerald-50 text-emerald-600",
              amber: "bg-amber-50 text-amber-600",
            };
            return (
              <div
                key={f.title}
                className={`flex flex-col md:flex-row items-start gap-5 md:gap-8 bg-white rounded-2xl border border-slate-200 p-6 md:p-8 ${
                  i % 2 === 1 ? "md:flex-row-reverse" : ""
                }`}
              >
                <div className={`rounded-2xl p-4 shrink-0 ${tones[f.tone]}`}>
                  <f.Icon className="h-9 w-9" />
                </div>
                <div className="space-y-2.5">
                  <h3 className="text-xl font-bold text-slate-900">{f.title}</h3>
                  <p className="text-slate-600 leading-relaxed">{f.body}</p>
                  {f.cta && (
                    <Link
                      href={f.cta.href}
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-700 hover:text-indigo-900"
                    >
                      {f.cta.label}
                      <IconArrowRight className="h-4 w-4" />
                    </Link>
                  )}
                  {f.links && (
                    <div className="flex flex-wrap gap-3 pt-1">
                      {f.links.map((l) => (
                        <Link
                          key={l.href}
                          href={l.href}
                          className="inline-flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-indigo-300 hover:text-indigo-700 transition"
                        >
                          <l.Icon className="h-4 w-4" />
                          {l.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </section>

        {/* How it works: the presentation narrative — one platform, two worlds */}
        <section className="max-w-4xl mx-auto space-y-5">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-slate-900">{t.hiwTitle}</h2>
            <p className="text-sm text-slate-500 max-w-2xl mx-auto">{t.hiwSub}</p>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { title: t.hiw1T, body: t.hiw1 },
              { title: t.hiw2T, body: t.hiw2 },
              { title: t.hiw3T, body: t.hiw3 },
            ].map((s, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 space-y-1.5">
                <p className="font-semibold text-indigo-700">{s.title}</p>
                <p className="text-sm text-slate-600 leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3 max-w-2xl mx-auto">
            {t.hiwFree}
          </p>
        </section>

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

        {/* Lawyer CTA */}
        <section className="max-w-3xl mx-auto bg-indigo-700 rounded-2xl p-6 md:p-8 text-white flex flex-col md:flex-row items-start md:items-center gap-5">
          <IconScale className="h-10 w-10 text-indigo-200 shrink-0" />
          <div className="flex-1 space-y-1.5">
            <h2 className="text-xl font-bold">{t.landLawT}</h2>
            <p className="text-sm text-indigo-100 leading-relaxed">{t.landLawB}</p>
          </div>
          <Link
            href="/per-avokatet"
            className="inline-flex items-center gap-1.5 bg-white text-indigo-700 font-semibold text-sm rounded-xl px-4 py-2.5 hover:bg-indigo-50 transition shrink-0"
          >
            {t.landLawCta}
            <IconArrowRight className="h-4 w-4" />
          </Link>
        </section>
      </main>
    </PublicShell>
  );
}
