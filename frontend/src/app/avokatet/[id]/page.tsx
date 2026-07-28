"use client";

// Dedicated lawyer profile — the 2026 directory pattern: the profile is the
// destination, not a feeder. Everything a citizen needs to decide lives here:
// trust signals as big numbers, reviews, transparent price, direct actions.
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { Card, Spinner } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import BookingWidget from "@/components/booking-widget";

interface ProfileReview {
  author: string;
  rating: number;
  comment: string;
  date: string;
}

interface LawyerProfileData {
  id: string;
  tenant_id: string;
  full_name: string;
  firm_name: string;
  bio: string | null;
  practice_areas: string[];
  cities: string[];
  languages: string[];
  photo: string | null;
  verified: boolean;
  founder: boolean;
  consult_fee_eur: number | null;
  rating: number | null;
  review_count: number;
  booking: boolean;
  years_experience: number | null;
  cases_completed: number;
  reviews: ProfileReview[];
  member_since: string;
}

const LANG_LABELS: Record<string, string> = {
  sq: "Shqip", sr: "Srpski", tr: "Türkçe", bs: "Bosanski", en: "English", zh: "中文",
};

function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-amber-500">
      {"★".repeat(Math.round(rating))}
      <span className="text-slate-300">{"★".repeat(5 - Math.round(rating))}</span>
    </span>
  );
}

export default function LawyerProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const [profile, setProfile] = useState<LawyerProfileData | null | "missing">(null);

  useEffect(() => {
    fetch(`/api/public/lawyers/${id}`)
      .then((res) => (res.ok ? res.json() : "missing"))
      .then(setProfile)
      .catch(() => setProfile("missing"));
  }, [id]);

  if (profile === null) {
    return (
      <PublicShell>
        <main className="w-full max-w-3xl mx-auto px-4 py-16 flex justify-center">
          <Spinner />
        </main>
      </PublicShell>
    );
  }

  if (profile === "missing") {
    return (
      <PublicShell>
        <main className="w-full max-w-3xl mx-auto px-4 py-16 text-center space-y-4">
          <p className="text-slate-500">{t.ppNotFound}</p>
          <Link href="/avokatet" className="text-indigo-600 font-medium hover:underline">
            ← {t.ppBackToDirectory}
          </Link>
        </main>
      </PublicShell>
    );
  }

  const memberYear = new Date(profile.member_since).getFullYear();

  return (
    <PublicShell>
      <main className="w-full max-w-3xl mx-auto px-4 py-8 space-y-6">
        <Link href="/avokatet" className="text-sm text-slate-400 hover:text-indigo-600">
          ← {t.ppBackToDirectory}
        </Link>

        {/* Identity block */}
        <div className="flex items-start gap-4 sm:gap-5">
          {profile.photo ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img
              src={profile.photo}
              alt={profile.full_name}
              className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl object-cover shrink-0"
            />
          ) : (
            <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center text-3xl font-bold shrink-0">
              {profile.full_name.charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <h1 className="text-2xl font-bold leading-tight">{profile.full_name}</h1>
            <p className="text-sm text-slate-500 truncate">{profile.firm_name}</p>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              <span className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 rounded-full px-2 py-0.5">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-3 w-3">
                  <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {t.lpVerified}
              </span>
              {profile.founder && (
                <span className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-amber-700 bg-amber-50 rounded-full px-2 py-0.5">
                  <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3">
                    <path d="M12 2l2.9 6.26L21 9.27l-4.5 4.38L17.8 21 12 17.77 6.2 21l1.3-7.35L3 9.27l6.1-1.01L12 2z" />
                  </svg>
                  {t.mkFounder}
                </span>
              )}
              {profile.cities.map((c) => (
                <span key={c} className="text-[11px] bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                  {c}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Trust signals as big numbers */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {profile.years_experience != null && profile.years_experience > 0 && (
            <Card className="p-4 text-center">
              <p className="text-2xl font-bold text-indigo-700">{profile.years_experience}</p>
              <p className="text-xs text-slate-500 mt-0.5">{t.lpYearsExp}</p>
            </Card>
          )}
          {profile.cases_completed > 0 && (
            <Card className="p-4 text-center">
              <p className="text-2xl font-bold text-indigo-700">{profile.cases_completed}</p>
              <p className="text-xs text-slate-500 mt-0.5">{t.lpCasesDone}</p>
            </Card>
          )}
          {profile.rating != null && profile.review_count > 0 && (
            <Card className="p-4 text-center">
              <p className="text-2xl font-bold text-indigo-700">{profile.rating.toFixed(1)}</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {profile.review_count} {t.lpReviewsWord}
              </p>
            </Card>
          )}
          <Card className="p-4 text-center">
            <p className="text-2xl font-bold text-indigo-700">{memberYear}</p>
            <p className="text-xs text-slate-500 mt-0.5">{t.ppMemberSince}</p>
          </Card>
        </div>

        {/* Actions: concrete, low-friction CTAs */}
        <Card className="p-5 space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/posto-rastin?avokati=${profile.tenant_id}`}
              className="inline-flex items-center justify-center rounded-xl bg-indigo-600 text-white text-sm font-semibold px-5 py-2.5 hover:bg-indigo-700 transition"
            >
              {t.mkContactLawyer} →
            </Link>
            {profile.booking && <BookingWidget profileId={profile.id} prominent />}
            {profile.consult_fee_eur != null && (
              <span className="text-sm text-slate-500">
                {t.lpConsultFrom} <b className="text-slate-700">{profile.consult_fee_eur} €</b>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">{t.ppFreeNote}</p>
        </Card>

        {/* About */}
        {profile.bio && (
          <section className="space-y-2">
            <h2 className="font-semibold">{t.ppAbout}</h2>
            <p className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed">
              {profile.bio}
            </p>
          </section>
        )}

        {/* Practice areas + languages */}
        <section className="space-y-2">
          <h2 className="font-semibold">{t.mkAllAreas}</h2>
          <div className="flex flex-wrap gap-1.5">
            {(profile.practice_areas.length ? profile.practice_areas : ["other"]).map((a) => (
              <span key={a} className="text-xs bg-indigo-50 text-indigo-700 rounded-full px-2.5 py-1">
                {t[a as keyof typeof t] as string}
              </span>
            ))}
            {profile.languages.map((l) => (
              <span key={l} className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-1">
                {LANG_LABELS[l] || l}
              </span>
            ))}
          </div>
        </section>

        {/* Client reviews (service experience, never legal outcomes) */}
        {profile.reviews.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-semibold">{t.ppReviews}</h2>
            {profile.reviews.map((r, i) => (
              <Card key={i} className="p-4 space-y-1.5">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium">{r.author}</p>
                  <Stars rating={r.rating} />
                </div>
                <p className="text-sm text-slate-600">{r.comment}</p>
                <p className="text-[11px] text-slate-400">
                  {new Date(r.date).toLocaleDateString(locale, {
                    day: "numeric", month: "long", year: "numeric",
                  })}
                </p>
              </Card>
            ))}
          </section>
        )}
      </main>
    </PublicShell>
  );
}
