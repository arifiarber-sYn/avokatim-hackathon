"use client";

/** Marketing page for the second paying profession: what notary offices get.
 * Mirror of /per-avokatet, adapted legally — no case marketplace, no promoted
 * placement; appointments + prepared parties instead. Violet accent matches
 * the notary pillar used across the public pages. */
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";

export default function ForNotariesPage() {
  const { t } = useI18n();

  const features = [t.npFeat1, t.npFeat2, t.npFeat3, t.npFeat4, t.npFeat5, t.npFeat6];

  return (
    <div className="min-h-screen bg-slate-900">
      <header className="border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-violet-400">
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
          <p className="inline-flex items-center rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-violet-300">
            {t.npBadge}
          </p>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1] bg-gradient-to-br from-white via-slate-200 to-violet-300 bg-clip-text text-transparent pb-1">
            {t.npTitle}
          </h1>
          <p className="text-slate-400 md:text-lg max-w-2xl mx-auto">{t.npSubtitle}</p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/regjistrohu?profesioni=noter"
              className="rounded-xl bg-violet-600 text-white px-7 py-3 text-sm font-semibold hover:bg-violet-500 shadow-lg shadow-violet-950 hover:-translate-y-0.5 transition-all duration-300"
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
          <p className="text-xs text-slate-500">{t.npPlanNote}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {features.map((f, i) => (
            <div
              key={i}
              className="bg-slate-800/60 rounded-2xl border border-slate-700/60 p-5 flex gap-3 hover:border-violet-500/50 hover:bg-slate-800 transition-colors duration-300"
            >
              <span className="shrink-0 h-6 w-6 rounded-full bg-violet-600/20 text-violet-400 flex items-center justify-center text-xs font-bold">
                {i + 1}
              </span>
              <p className="text-sm text-slate-300">{f}</p>
            </div>
          ))}
        </div>

        {/* How the adapted "marketplace" works: appointments + prepared parties */}
        <div className="max-w-3xl mx-auto space-y-4">
          <h2 className="text-xl font-bold text-white text-center">{t.npHiwT}</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {[t.npHiw1, t.npHiw2, t.npHiw3].map((step, i) => (
              <div key={i} className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-5 space-y-2">
                <span className="inline-flex h-7 w-7 rounded-full bg-violet-600 text-white items-center justify-center text-xs font-bold">
                  {i + 1}
                </span>
                <p className="text-sm text-slate-300 leading-relaxed">{step}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Ethical guardrail: equal listing, official tariffs, no case race */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-gradient-to-br from-violet-500/10 to-slate-800/60 rounded-xl border border-violet-500/30 p-6 text-center space-y-2">
            <span className="text-xl">⚖️</span>
            <h2 className="text-lg font-bold text-white">{t.npEthicsT}</h2>
            <p className="text-sm text-slate-300">{t.npEthicsB}</p>
          </div>
        </div>

        {/* Security promise: links to the public /siguria page */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-5 flex items-start gap-3">
            <span className="text-xl">🔐</span>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-white">{t.secTitle}</p>
              <p className="text-sm text-slate-400">
                {t.secEncT} · {t.secLocalT} · {t.secBackupT}{" "}
                <Link href="/siguria" className="text-violet-400 hover:text-violet-300 underline">
                  {t.ftSecurity} →
                </Link>
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-2xl mx-auto space-y-4">
          <h2 className="text-xl font-bold text-white text-center">{t.lpPlansTitle}</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-5">
              <p className="text-sm text-slate-300">{t.lpPlanTrial}</p>
            </div>
            <div className="bg-violet-600/10 rounded-xl border border-violet-500/40 p-5">
              <p className="text-sm text-slate-200">{t.npPlanNote}</p>
            </div>
          </div>
          <div className="text-center pt-2">
            <Link
              href="/regjistrohu?profesioni=noter"
              className="inline-block rounded-lg bg-violet-600 text-white px-6 py-3 text-sm font-semibold hover:bg-violet-500"
            >
              {t.lpCta}
            </Link>
          </div>
        </div>

        <footer className="text-center text-xs text-slate-500 space-x-4 border-t border-slate-800 pt-6">
          <Link href="/" className="hover:underline">AvokatIM</Link>
          <Link href="/noteret" className="hover:underline">{t.pnNotaries}</Link>
          <Link href="/per-avokatet" className="hover:underline">{t.mkForLawyersLink}</Link>
          <Link href="/kushtet" className="hover:underline">{t.termsOfService}</Link>
          <Link href="/privatesia" className="hover:underline">{t.privacyPolicy}</Link>
          <Link href="/siguria" className="hover:underline">{t.ftSecurity}</Link>
          <Link href="/kontakti" className="hover:underline">{t.ctTitle}</Link>
        </footer>
      </main>
    </div>
  );
}
