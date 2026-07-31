"use client";

// Public security page: how AvokatIM protects documents and data.
// Static content, 6 languages, no account needed.
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import { IconScale } from "@/components/icons";

export default function SecurityPage() {
  const { t } = useI18n();

  const items: { icon: string; title: string; body: string }[] = [
    { icon: "🔐", title: t.secEncT, body: t.secEncB },
    { icon: "🖥️", title: t.secLocalT, body: t.secLocalB },
    { icon: "⛓️", title: t.secChainT, body: t.secChainB },
    { icon: "🔌", title: t.secKillT, body: t.secKillB },
    { icon: "💾", title: t.secBackupT, body: t.secBackupB },
    { icon: "⚖️", title: t.secLawT, body: t.secLawB },
  ];

  return (
    <PublicShell>
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 text-indigo-600">
            <IconScale className="h-8 w-8" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            {t.secTitle}
          </h1>
          <p className="text-slate-600 max-w-2xl mx-auto leading-relaxed">
            {t.secSubtitle}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          {items.map((item) => (
            <div
              key={item.title}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-2"
            >
              <p className="text-2xl">{item.icon}</p>
              <h2 className="font-semibold text-slate-900">{item.title}</h2>
              <p className="text-sm text-slate-600 leading-relaxed">{item.body}</p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-6 space-y-2">
          <p className="text-2xl">🛡️</p>
          <h2 className="font-semibold text-slate-900">{t.secVulnT}</h2>
          <p className="text-sm text-slate-600 leading-relaxed">{t.secVulnB}</p>
          <Link
            href="/kontakti"
            className="inline-block text-sm font-medium text-indigo-600 hover:text-indigo-800 underline"
          >
            {t.ftContact}
          </Link>
        </div>

        <div className="bg-slate-900 text-slate-200 rounded-2xl p-6 text-center space-y-3">
          <p className="text-sm leading-relaxed">{t.secFooterNote}</p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <Link href="/privatesia" className="text-indigo-300 hover:text-white underline">
              {t.privacyPolicy}
            </Link>
            <Link href="/kontakti" className="text-indigo-300 hover:text-white underline">
              {t.ftContact}
            </Link>
          </div>
        </div>
      </div>
    </PublicShell>
  );
}
