"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getToken, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Textarea } from "@/components/ui";
import PublicShell from "@/components/public-shell";

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
      <main className="w-full max-w-5xl mx-auto px-4 py-10 md:py-16 space-y-10">
        {/* Hero: one primary action — ask Ava (JustAnswer pattern) */}
        <div className="max-w-2xl mx-auto text-center space-y-4">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">{t.mkHeroTitle}</h1>
          <p className="text-slate-500">{t.mkHeroCitizen}</p>
          <form onSubmit={askAva} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-3 space-y-2 text-left">
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
              <p className="text-xs text-slate-400 hidden sm:block">{t.mkAvaDisclaimer.split(".")[0]}.</p>
              <Button type="submit" className="shrink-0">{t.mkAskAva}</Button>
            </div>
          </form>
        </div>

        {/* Secondary paths */}
        <div className="grid sm:grid-cols-3 gap-4 max-w-3xl mx-auto">
          <Link
            href="/avokatet"
            className="bg-white rounded-xl border border-slate-200 p-5 hover:border-indigo-300 hover:shadow-sm transition"
          >
            <p className="font-semibold text-slate-900">{t.mkFindLawyer}</p>
            <p className="text-xs text-slate-500 mt-1">{t.mkLawyersDirectory}</p>
          </Link>
          <Link
            href="/posto-rastin"
            className="bg-white rounded-xl border border-slate-200 p-5 hover:border-indigo-300 hover:shadow-sm transition"
          >
            <p className="font-semibold text-slate-900">{t.mkPostCase}</p>
            <p className="text-xs text-slate-500 mt-1">{t.mkHeroCitizen.split("—")[0]}</p>
          </Link>
          <Link
            href="/rasti-im?sos=1"
            className="bg-red-600 rounded-xl p-5 hover:bg-red-700 transition"
          >
            <p className="font-bold text-white">{t.mkSos}</p>
            <p className="text-xs text-red-100 mt-1">{t.mkSosDutyHint}</p>
          </Link>
        </div>

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

        <footer className="text-center text-xs text-slate-400 space-x-4 pt-4">
          <Link href="/per-avokatet" className="hover:underline">{t.mkForLawyersLink}</Link>
          <Link href="/portal" className="hover:underline">{t.portalTitle}</Link>
          <Link href="/kushtet" className="hover:underline">{t.termsOfService}</Link>
          <Link href="/privatesia" className="hover:underline">{t.privacyPolicy}</Link>
        </footer>
      </main>
    </PublicShell>
  );
}
