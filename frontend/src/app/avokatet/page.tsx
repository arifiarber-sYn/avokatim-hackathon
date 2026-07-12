"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { LOCALES } from "@/lib/dictionaries";
import { citizenPost, getCitizenToken, PublicLawyer } from "@/lib/citizen";
import { Button, Card, ErrorNote, Input, Select, Spinner, Textarea } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";

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

        {filtered === null ? (
          <Spinner />
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
                      <span className="truncate">{lawyer.full_name}</span>
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
                    href={`/posto-rastin?avokati=${lawyer.tenant_id}`}
                    className="inline-block text-sm font-medium text-indigo-600 hover:underline"
                  >
                    {t.mkContactLawyer} →
                  </Link>
                  {lawyer.consult_fee_eur != null && (
                    <span className="text-xs text-slate-500">
                      {t.lpConsultFrom} <b className="text-slate-700">{lawyer.consult_fee_eur} €</b>
                    </span>
                  )}
                </div>
                {lawyer.booking && <BookingWidget profileId={lawyer.id} />}
              </Card>
            ))}
          </div>
        )}
      </main>
    </PublicShell>
  );
}

/** Inline slot picker: fetch free 30-min slots and reserve one (citizen auth). */
function BookingWidget({ profileId }: { profileId: string }) {
  const { t, locale } = useI18n();
  const [open, setOpen] = useState(false);
  const [slots, setSlots] = useState<string[] | null>(null);
  const [picked, setPicked] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function openPicker() {
    setOpen(true);
    if (slots !== null) return;
    try {
      const res = await fetch(`/api/public/lawyers/${profileId}/slots`);
      const data = await res.json();
      setSlots(data.slots || []);
    } catch {
      setSlots([]);
    }
  }

  async function book(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await citizenPost("/citizen/bookings", {
        profile_id: profileId,
        starts_at: picked,
        note: note.trim() || null,
      });
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <p className="text-xs bg-emerald-50 text-emerald-700 rounded-lg px-3 py-2">{t.bkBooked}</p>
    );
  }

  if (!open) {
    return (
      <button
        onClick={openPicker}
        className="text-sm font-medium text-emerald-700 hover:underline"
      >
        📅 {t.bkBook}
      </button>
    );
  }

  if (!getCitizenToken()) {
    return (
      <p className="text-xs bg-amber-50 text-amber-800 rounded-lg px-3 py-2">
        {t.bkLoginFirst}{" "}
        <Link href="/rasti-im" className="underline font-medium">
          {t.mkMyCase} →
        </Link>
      </p>
    );
  }

  // Group upcoming slots by day for a compact picker
  const byDay = new Map<string, string[]>();
  for (const s of slots || []) {
    const day = new Date(s).toLocaleDateString(locale, {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
    byDay.set(day, [...(byDay.get(day) || []), s]);
  }

  return (
    <div className="border-t border-slate-100 pt-3 space-y-2">
      <p className="text-xs font-semibold text-slate-600">{t.bkPickSlot}</p>
      {slots === null ? (
        <Spinner />
      ) : slots.length === 0 ? (
        <p className="text-xs text-slate-500">{t.bkNoSlots}</p>
      ) : (
        <form onSubmit={book} className="space-y-2">
          <div className="space-y-1.5 max-h-44 overflow-y-auto">
            {[...byDay.entries()].map(([day, daySlots]) => (
              <div key={day} className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] text-slate-400 w-24 shrink-0">{day}</span>
                {daySlots.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setPicked(s)}
                    className={`text-xs rounded-md px-2 py-1 border transition ${
                      picked === s
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300"
                    }`}
                  >
                    {new Date(s).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}
                  </button>
                ))}
              </div>
            ))}
          </div>
          {picked && (
            <>
              <Textarea
                rows={2}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder={t.bkNote}
              />
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy} className="w-full">
                {busy ? t.loading : t.bkConfirmBook}
              </Button>
            </>
          )}
        </form>
      )}
    </div>
  );
}
