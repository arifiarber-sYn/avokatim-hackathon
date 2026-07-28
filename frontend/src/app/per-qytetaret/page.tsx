"use client";

/**
 * The citizen story page: everything a citizen gets, told as a narrative —
 * ask Ava right away, four feature sections, how it works, free tools.
 */
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { Button, Textarea } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import {
  IconArrowRight,
  IconCalendar,
  IconChat,
  IconDoc,
  IconLock,
  IconScale,
  IconShield,
  IconUsers,
} from "@/components/icons";

export default function ForCitizensPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [question, setQuestion] = useState("");

  function askAva(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (q) localStorage.setItem("avokatim_ava_prefill", q.slice(0, 2000));
    router.push("/ava");
  }

  return (
    <PublicShell wide>
      {/* Hero: one primary action — ask Ava */}
      <section className="hero-backdrop bg-white border-b border-slate-100">
        <div className="max-w-5xl mx-auto px-4 pt-12 pb-10 md:pt-18 md:pb-14">
          <div className="max-w-2xl mx-auto text-center space-y-4 fade-in-up">
            <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1] text-hero-gradient bg-clip-text text-transparent pb-1">
              {t.mkHeroTitle}
            </h1>
            <p className="text-slate-500 md:text-lg">{t.mkHeroCitizen}</p>
            <form
              onSubmit={askAva}
              className="bg-white/90 backdrop-blur rounded-2xl ring-1 ring-slate-200 shadow-lg shadow-indigo-100/60 p-3 space-y-2 text-left focus-within:ring-indigo-300 transition"
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
          </div>

          {/* Secondary paths */}
          <div className="fade-in-up-d1 grid sm:grid-cols-3 gap-4 max-w-3xl mx-auto mt-10">
            <Link
              href="/avokatet"
              className="bg-white/90 backdrop-blur rounded-2xl ring-1 ring-slate-200 p-5 hover:ring-indigo-300 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300"
            >
              <IconUsers className="h-6 w-6 text-indigo-600 mb-2" />
              <p className="font-semibold text-slate-900">{t.mkFindLawyer}</p>
              <p className="text-xs text-slate-500 mt-1">{t.mkLawyersDirectory}</p>
            </Link>
            <Link
              href="/posto-rastin"
              className="bg-white/90 backdrop-blur rounded-2xl ring-1 ring-slate-200 p-5 hover:ring-indigo-300 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300"
            >
              <IconDoc className="h-6 w-6 text-indigo-600 mb-2" />
              <p className="font-semibold text-slate-900">{t.mkPostCase}</p>
              <p className="text-xs text-slate-500 mt-1">{t.mkHeroCitizen.split("—")[0]}</p>
            </Link>
            <Link
              href="/rasti-im?sos=1"
              className="bg-gradient-to-br from-red-600 to-red-700 rounded-2xl p-5 shadow-md shadow-red-200 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300"
            >
              <IconShield className="h-6 w-6 text-red-100 mb-2" />
              <p className="font-bold text-white">{t.mkSos}</p>
              <p className="text-xs text-red-100 mt-1">{t.mkSosDutyHint}</p>
            </Link>
          </div>
        </div>
      </section>

      <main className="w-full max-w-5xl mx-auto px-4 py-12 space-y-16">
        {/* Four alternating feature sections — the citizen story */}
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
              links: [{ href: "/siguria", label: t.landSosSecLink, Icon: IconLock }],
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
            {
              Icon: IconScale,
              tone: "violet",
              title: t.landNotaryT,
              body: t.landNotaryB,
              cta: { href: "/noteret", label: t.landNotaryCta },
              links: [{ href: "/dokumentet", label: t.landNotaryDocsLink, Icon: IconDoc }],
            },
          ].map((f, i) => {
            const tones: Record<string, string> = {
              indigo: "bg-indigo-50 text-indigo-600",
              red: "bg-red-50 text-red-600",
              emerald: "bg-emerald-50 text-emerald-600",
              amber: "bg-amber-50 text-amber-600",
              violet: "bg-violet-50 text-violet-600",
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

        {/* How it works */}
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

        {/* FAQ — the questions people actually ask Ava, mirrored as FAQPage
            JSON-LD in the server layout for search/AI answers */}
        <section className="max-w-3xl mx-auto space-y-5">
          <h2 className="text-2xl font-bold text-slate-900 text-center">{t.faqTitle}</h2>
          <div className="space-y-2">
            {([1, 2, 3, 4, 5, 6] as const).map((n) => {
              const dict = t as unknown as Record<string, string>;
              return (
                <details
                  key={n}
                  className="group bg-white rounded-xl border border-slate-200 px-5 py-4 open:border-indigo-200"
                >
                  <summary className="cursor-pointer list-none flex items-center justify-between gap-3 font-semibold text-slate-800 text-sm md:text-base">
                    {dict[`faqQ${n}`]}
                    <span className="shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-xl leading-none">
                      +
                    </span>
                  </summary>
                  <p className="text-sm text-slate-600 leading-relaxed mt-3">
                    {dict[`faqA${n}`]}
                  </p>
                </details>
              );
            })}
          </div>
        </section>
      </main>
    </PublicShell>
  );
}
