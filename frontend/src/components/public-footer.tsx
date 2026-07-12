"use client";

/**
 * Shared footer for all public (citizen-facing) pages. Four columns on
 * desktop, stacked on mobile: platform blurb, citizen links, lawyer links,
 * legal & contact. Mounted once inside PublicShell.
 */
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { IconScale } from "@/components/icons";

export default function PublicFooter() {
  const { t } = useI18n();

  const col = "space-y-2 text-sm";
  const link = "block text-slate-400 hover:text-white transition-colors";

  return (
    <footer className="bg-slate-900 text-slate-300 mt-16">
      <div className="max-w-5xl mx-auto px-4 py-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <IconScale className="h-6 w-6 text-indigo-400" />
            <span className="text-lg font-bold text-white">
              Avokat<span className="text-indigo-400">IM</span>
            </span>
          </div>
          <p className="text-sm text-slate-400 leading-relaxed">{t.ftTagline}</p>
        </div>

        <div className={col}>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            {t.ftCitizens}
          </div>
          <Link href="/per-qytetaret" className={link}>{t.umbCitizenT}</Link>
          <Link href="/ava" className={link}>Ava</Link>
          <Link href="/avokatet" className={link}>{t.pnLawyers}</Link>
          <Link href="/posto-rastin" className={link}>{t.pnPost}</Link>
          <Link href="/rasti-im?sos=1" className={link}>SOS</Link>
          <Link href="/afatet" className={link}>{t.dcTitle}</Link>
          <Link href="/dokumentet" className={link}>{t.cdTitle}</Link>
          <Link href="/kycu" className={link}>{t.acctLoginT}</Link>
          <Link href="/llogaria" className={link}>{t.acctTitle}</Link>
        </div>

        <div className={col}>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            {t.ftLawyersCol}
          </div>
          <Link href="/per-avokatet" className={link}>{t.ftJoin}</Link>
          <Link href="/login" className={link}>{t.ftLogin}</Link>
          <Link href="/portal" className={link}>{t.ftPortal}</Link>
        </div>

        <div className={col}>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            {t.ftLegalCol}
          </div>
          <Link href="/kushtet" className={link}>{t.termsOfService}</Link>
          <Link href="/privatesia" className={link}>{t.privacyPolicy}</Link>
          <Link href="/kontakti" className={link}>{t.ftContact}</Link>
        </div>
      </div>
      <div className="border-t border-slate-800">
        <div className="max-w-5xl mx-auto px-4 py-4 text-xs text-slate-500 flex flex-wrap items-center justify-between gap-2">
          <span>© {new Date().getFullYear()} AvokatIM</span>
          <span className="text-slate-400">
            Krijuar nga <span className="font-semibold text-slate-300">Arbër Arifi</span>
            {" & "}
            <span className="font-semibold text-slate-300">Fable 5</span>
            {" · Kushtuar "}
            <span className="font-semibold text-indigo-300">Borës</span>
          </span>
          <span>Kosovë · avokatiim.ai</span>
        </div>
      </div>
    </footer>
  );
}
