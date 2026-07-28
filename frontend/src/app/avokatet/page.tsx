"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { LOCALES } from "@/lib/dictionaries";
import { PublicLawyer } from "@/lib/citizen";
import { Card, Input, Select } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import BookingWidget from "@/components/booking-widget";

const AREAS = ["civil", "criminal", "family", "commercial", "labor", "administrative", "other"] as const;

export default function LawyerDirectoryPage() {
  const { t } = useI18n();
  const [lawyers, setLawyers] = useState<PublicLawyer[] | null>(null);
  const [area, setArea] = useState("");
  const [city, setCity] = useState("");
  const [language, setLanguage] = useState("");

  useEffect(() => {
    fetch("/api/public/lawyers")
      .then((res) => res.json())
      .then(setLawyers)
      .catch(() => setLawyers([]));
  }, []);

  const filtered = useMemo(() => {
    if (!lawyers) return null;
    return lawyers.filter((l) => {
      if (area && !l.practice_areas.includes(area)) return false;
      if (city && !l.cities.some((c) => c.toLowerCase().includes(city.toLowerCase()))) return false;
      if (language && !l.languages.includes(language)) return false;
      return true;
    });
  }, [lawyers, area, city, language]);

  return (
    <PublicShell wide>
      <main className="w-full max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t.mkLawyersDirectory}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.mkDisclaimer}</p>
        </div>

        <PageIntro k="avokatet" title={t.lawyersIntroT} body={t.lawyersIntro} />

        {/* Sticky filter bar: stays visible while scrolling the directory */}
        <div className="sticky top-[57px] z-30 -mx-4 px-4 py-2.5 bg-slate-50/90 backdrop-blur border-b border-slate-100">
          <div className="grid md:grid-cols-3 gap-3">
            <Select value={area} onChange={(e) => setArea(e.target.value)}>
              <option value="">{t.mkAllAreas}</option>
              {AREAS.map((a) => (
                <option key={a} value={a}>{t[a]}</option>
              ))}
            </Select>
            <Input placeholder={t.mkCity} value={city} onChange={(e) => setCity(e.target.value)} />
            <Select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="">{t.mkLanguagesLabel}</option>
              {LOCALES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </Select>
          </div>
        </div>

        {filtered === null ? (
          <div className="grid md:grid-cols-2 gap-4" aria-hidden="true">
            {[0, 1, 2, 3].map((i) => (
              <Card key={i} className="p-5 space-y-3 animate-pulse">
                <div className="flex items-start gap-3">
                  <div className="h-12 w-12 rounded-full bg-slate-200 shrink-0" />
                  <div className="flex-1 space-y-2 pt-1">
                    <div className="h-3.5 bg-slate-200 rounded w-2/3" />
                    <div className="h-3 bg-slate-100 rounded w-1/2" />
                  </div>
                </div>
                <div className="h-3 bg-slate-100 rounded w-full" />
                <div className="h-3 bg-slate-100 rounded w-4/5" />
                <div className="flex gap-1.5">
                  <div className="h-5 w-16 bg-slate-100 rounded-full" />
                  <div className="h-5 w-20 bg-slate-100 rounded-full" />
                </div>
              </Card>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <Card className="p-8 text-center text-sm text-slate-500">{t.noResults}</Card>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {filtered.map((lawyer) => (
              <Card
                key={lawyer.id}
                className={`p-5 space-y-3 ${lawyer.highlighted ? "ring-1 ring-indigo-200 border-indigo-200" : ""}`}
              >
                <div className="flex items-start gap-3">
                  {lawyer.photo ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={lawyer.photo} alt="" className="h-12 w-12 rounded-full object-cover" />
                  ) : (
                    <div className="h-12 w-12 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
                      {lawyer.full_name.charAt(0)}
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className="font-semibold truncate flex items-center gap-1.5">
                      <Link
                        href={`/avokatet/${lawyer.id}`}
                        className="truncate hover:text-indigo-700 hover:underline"
                      >
                        {lawyer.full_name}
                      </Link>
                      {lawyer.verified && (
                        <span
                          className="inline-flex items-center gap-0.5 shrink-0 text-[11px] font-semibold text-emerald-700 bg-emerald-50 rounded-full px-1.5 py-0.5"
                          title={t.lpVerified}
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-3 w-3">
                            <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          {t.lpVerified}
                        </span>
                      )}
                      {lawyer.founder && (
                        <span
                          className="inline-flex items-center gap-0.5 shrink-0 text-[11px] font-semibold text-amber-700 bg-amber-50 rounded-full px-1.5 py-0.5"
                          title={t.mkFounder}
                        >
                          <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3">
                            <path d="M12 2l2.9 6.26L21 9.27l-4.5 4.38L17.8 21 12 17.77 6.2 21l1.3-7.35L3 9.27l6.1-1.01L12 2z" />
                          </svg>
                          {t.mkFounder}
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-slate-500 truncate">{lawyer.firm_name}</p>
                    {lawyer.rating != null && (
                      <p className="text-xs text-amber-600 mt-0.5">
                        {"★".repeat(Math.round(lawyer.rating))}
                        <span className="text-slate-400">
                          {"★".repeat(5 - Math.round(lawyer.rating))}
                        </span>{" "}
                        <span className="text-slate-500">
                          {lawyer.rating.toFixed(1)} · {lawyer.review_count} {t.lpReviewsWord}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
                {lawyer.bio && <p className="text-sm text-slate-600 line-clamp-3">{lawyer.bio}</p>}
                {/* Trust chips: experience, verified platform activity, price */}
                {(lawyer.years_experience != null ||
                  (lawyer.cases_completed ?? 0) > 0 ||
                  lawyer.consult_fee_eur != null ||
                  (lawyer.flat_services?.length ?? 0) > 0) && (
                  <div className="flex flex-wrap gap-1.5">
                    {lawyer.years_experience != null && lawyer.years_experience > 0 && (
                      <span className="text-xs font-medium bg-sky-50 text-sky-700 rounded-full px-2 py-0.5">
                        {lawyer.years_experience} {t.lpYearsExp}
                      </span>
                    )}
                    {(lawyer.cases_completed ?? 0) > 0 && (
                      <span className="text-xs font-medium bg-emerald-50 text-emerald-700 rounded-full px-2 py-0.5">
                        {lawyer.cases_completed} {t.lpCasesDone}
                      </span>
                    )}
                    {lawyer.consult_fee_eur != null && (
                      <span className="text-xs font-medium bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                        {t.lpConsultFrom} {lawyer.consult_fee_eur} €
                      </span>
                    )}
                    {(lawyer.flat_services?.length ?? 0) > 0 && (
                      <span className="text-xs font-medium bg-violet-50 text-violet-700 rounded-full px-2 py-0.5">
                        {t.fsChip}
                      </span>
                    )}
                  </div>
                )}
                <div className="flex flex-wrap gap-1.5">
                  {lawyer.practice_areas.map((a) => (
                    <span key={a} className="text-xs bg-indigo-50 text-indigo-700 rounded-full px-2 py-0.5">
                      {t[a as keyof typeof t] as string}
                    </span>
                  ))}
                  {lawyer.cities.map((c) => (
                    <span key={c} className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                      {c}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between gap-3">
                  <Link
                    href={`/avokatet/${lawyer.id}`}
                    className="inline-block text-sm font-semibold text-indigo-600 hover:underline"
                  >
                    {t.lpViewProfile} →
                  </Link>
                  <Link
                    href={`/posto-rastin?avokati=${lawyer.tenant_id}`}
                    className="inline-block text-sm font-medium text-slate-500 hover:text-indigo-600 hover:underline"
                  >
                    {t.mkContactLawyer}
                  </Link>
                </div>
                {lawyer.booking && <BookingWidget profileId={lawyer.id} prominent />}
              </Card>
            ))}
          </div>
        )}
      </main>
    </PublicShell>
  );
}

