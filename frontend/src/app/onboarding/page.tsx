"use client";

/**
 * Lawyer onboarding wizard, shown right after signup. Three steps:
 * 1) public profile (visibility, practice areas, cities, languages, bio),
 * 2) OAK license + consultation fee, 3) optional weekly booking hours.
 * Every step can be skipped; the dashboard nudge remains as fallback.
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiGet, apiPut, getToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, Textarea } from "@/components/ui";

const AREAS = ["civil", "criminal", "family", "commercial", "labor", "administrative", "other"];
const LANGS: { code: string; label: string }[] = [
  { code: "sq", label: "Shqip" },
  { code: "sr", label: "Srpski" },
  { code: "tr", label: "Türkçe" },
  { code: "bs", label: "Bosanski" },
  { code: "en", label: "English" },
  { code: "zh", label: "中文" },
];

interface BookingWindow {
  day: number;
  start: string;
  end: string;
}

export default function OnboardingPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // Notary offices get a shorter variant: no practice areas, no custom
  // consultation fee (fixed tariffs), ONK license instead of OAK
  const [isNotary, setIsNotary] = useState(false);
  const [profile, setProfile] = useState({
    is_visible: true,
    sos_on_duty: false,
    bio: "",
    practice_areas: [] as string[],
    cities: "",
    languages: ["sq"] as string[],
    photo: null as string | null,
    oak_license_no: "",
    consult_fee_eur: "",
    career_start_year: "",
  });
  const [bookingEnabled, setBookingEnabled] = useState(false);
  const [windows, setWindows] = useState<BookingWindow[]>([]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    apiGet<{ tenant_profession?: string }>("/auth/me")
      .then((m) => setIsNotary(m.tenant_profession === "notary"))
      .catch(() => {});
    apiGet<{
      is_visible: boolean;
      bio: string | null;
      practice_areas: string[];
      cities: string[];
      languages: string[];
      oak_license_no: string | null;
      consult_fee_eur: number | null;
      career_start_year: number | null;
    }>("/marketplace/profile")
      .then((p) => {
        setProfile((prev) => ({
          ...prev,
          bio: p.bio || "",
          practice_areas: p.practice_areas.length ? p.practice_areas : prev.practice_areas,
          cities: p.cities.join(", "),
          languages: p.languages.length ? p.languages : prev.languages,
          oak_license_no: p.oak_license_no || "",
          consult_fee_eur: p.consult_fee_eur == null ? "" : String(p.consult_fee_eur),
          career_start_year: p.career_start_year == null ? "" : String(p.career_start_year),
        }));
      })
      .catch(() => {});
  }, [router]);

  function toggle(list: string[], value: string): string[] {
    return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
  }

  async function saveProfile(): Promise<boolean> {
    setError("");
    setBusy(true);
    try {
      await apiPut("/marketplace/profile", {
        is_visible: profile.is_visible,
        sos_on_duty: profile.sos_on_duty,
        bio: profile.bio || null,
        practice_areas: profile.practice_areas,
        cities: profile.cities.split(",").map((c) => c.trim()).filter(Boolean),
        languages: profile.languages,
        photo: profile.photo,
        oak_license_no: profile.oak_license_no.trim() || null,
        consult_fee_eur: profile.consult_fee_eur === "" ? null : Number(profile.consult_fee_eur),
        career_start_year:
          profile.career_start_year === "" ? null : Number(profile.career_start_year),
      });
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function saveBooking(): Promise<boolean> {
    if (!bookingEnabled || windows.length === 0) return true;
    setBusy(true);
    try {
      await apiPut("/marketplace/booking-settings", { enabled: true, slots: windows });
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      return false;
    } finally {
      setBusy(false);
    }
  }

  const dayName = (day: number) =>
    new Date(Date.UTC(2024, 0, 1 + day)).toLocaleDateString(locale, {
      weekday: "long",
      timeZone: "UTC",
    });

  function toggleDay(day: number) {
    setWindows((prev) =>
      prev.some((w) => w.day === day)
        ? prev.filter((w) => w.day !== day)
        : [...prev, { day, start: "09:00", end: "16:00" }]
    );
  }

  function setTime(day: number, field: "start" | "end", value: string) {
    setWindows((prev) => prev.map((w) => (w.day === day ? { ...w, [field]: value } : w)));
  }

  const stepLabels = [t.obStep1, t.obStep2, t.obStep3];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50 p-4 md:py-10">
      <div className="max-w-2xl mx-auto space-y-5">
        <div className="text-center space-y-1.5">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900">{t.obTitle}</h1>
          <p className="text-sm text-slate-500 max-w-lg mx-auto">
            {isNotary ? t.obSubtitleNotary : t.obSubtitle}
          </p>
        </div>

        {step <= 3 && (
          <div className="flex items-center justify-center gap-2">
            {stepLabels.map((label, i) => (
              <div key={i} className="flex items-center gap-2">
                <span
                  className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold ${
                    step > i + 1
                      ? "bg-emerald-500 text-white"
                      : step === i + 1
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-200 text-slate-500"
                  }`}
                >
                  {step > i + 1 ? "✓" : i + 1}
                </span>
                <span
                  className={`text-xs hidden sm:block ${
                    step === i + 1 ? "font-semibold text-slate-900" : "text-slate-500"
                  }`}
                >
                  {label}
                </span>
                {i < 2 && <span className="w-6 h-px bg-slate-300" />}
              </div>
            ))}
          </div>
        )}

        {step === 1 && (
          <Card className="p-6 space-y-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer font-medium">
              <input
                type="checkbox"
                checked={profile.is_visible}
                onChange={(e) => setProfile({ ...profile, is_visible: e.target.checked })}
                className="accent-indigo-600"
              />
              {isNotary ? t.mkVisibleInNotaryDirectory : t.mkVisibleInDirectory}
            </label>
            {!isNotary && (
            <div>
              <Label>{t.practiceArea}</Label>
              <div className="flex flex-wrap gap-2">
                {AREAS.map((a) => (
                  <button
                    key={a}
                    type="button"
                    onClick={() =>
                      setProfile({ ...profile, practice_areas: toggle(profile.practice_areas, a) })
                    }
                    className={`text-xs rounded-full px-3 py-1.5 border transition ${
                      profile.practice_areas.includes(a)
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-slate-600 border-slate-300 hover:border-indigo-300"
                    }`}
                  >
                    {t[a as keyof typeof t] as string}
                  </button>
                ))}
              </div>
            </div>
            )}
            <div>
              <Label>{t.mkCities}</Label>
              <Input
                value={profile.cities}
                onChange={(e) => setProfile({ ...profile, cities: e.target.value })}
                placeholder="Prishtinë, Prizren"
              />
            </div>
            <div>
              <Label>{t.mkLanguagesLabel}</Label>
              <div className="flex flex-wrap gap-2">
                {LANGS.map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    onClick={() =>
                      setProfile({ ...profile, languages: toggle(profile.languages, l.code) })
                    }
                    className={`text-xs rounded-full px-3 py-1.5 border transition ${
                      profile.languages.includes(l.code)
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-slate-600 border-slate-300 hover:border-indigo-300"
                    }`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label>{t.mkBio}</Label>
              <Textarea
                rows={3}
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                maxLength={4000}
              />
            </div>
            <ErrorNote message={error} />
            <div className="flex items-center justify-between pt-1">
              <Link href="/dashboard?welcome=1" className="text-xs text-slate-400 hover:text-slate-600">
                {t.obSkip}
              </Link>
              <Button onClick={() => setStep(2)} disabled={busy}>
                {t.obNext}
              </Button>
            </div>
          </Card>
        )}

        {step === 2 && (
          <Card className="p-6 space-y-4">
            <div>
              <Label>{isNotary ? t.mkOnkLicense : t.mkOakLicense}</Label>
              <Input
                value={profile.oak_license_no}
                onChange={(e) => setProfile({ ...profile, oak_license_no: e.target.value })}
                placeholder="p.sh. 1234"
                maxLength={64}
              />
              <p className="text-xs text-slate-500 mt-1">
                {isNotary ? t.mkOnkLicenseHint : t.mkOakLicenseHint}
              </p>
            </div>
            {!isNotary && (
            <div>
              <Label>{t.mkConsultFee}</Label>
              <Input
                type="number"
                min={0}
                max={10000}
                value={profile.consult_fee_eur}
                onChange={(e) => setProfile({ ...profile, consult_fee_eur: e.target.value })}
                placeholder="p.sh. 30"
              />
              <p className="text-xs text-slate-500 mt-1">{t.mkConsultFeeHint}</p>
            </div>
            )}
            <div>
              <Label>{t.mkCareerStart}</Label>
              <Input
                type="number"
                min={1950}
                max={new Date().getFullYear()}
                value={profile.career_start_year}
                onChange={(e) => setProfile({ ...profile, career_start_year: e.target.value })}
                placeholder="p.sh. 2010"
              />
              <p className="text-xs text-slate-500 mt-1">{t.mkCareerStartHint}</p>
            </div>
            <ErrorNote message={error} />
            <div className="flex items-center justify-between pt-1">
              <button
                onClick={() => setStep(1)}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                ← {t.obBack}
              </button>
              <Button
                onClick={async () => {
                  if (await saveProfile()) setStep(3);
                }}
                disabled={busy}
              >
                {busy ? t.loading : t.obNext}
              </Button>
            </div>
          </Card>
        )}

        {step === 3 && (
          <Card className="p-6 space-y-4">
            <p className="text-xs text-slate-500">{t.obBookHint}</p>
            <label className="flex items-center gap-2 text-sm cursor-pointer font-medium">
              <input
                type="checkbox"
                checked={bookingEnabled}
                onChange={(e) => setBookingEnabled(e.target.checked)}
                className="accent-indigo-600"
              />
              {t.bkEnable}
            </label>
            {bookingEnabled && (
              <div className="space-y-2">
                {[0, 1, 2, 3, 4, 5, 6].map((day) => {
                  const w = windows.find((x) => x.day === day);
                  return (
                    <div key={day} className="flex items-center gap-3 flex-wrap">
                      <label className="flex items-center gap-2 text-sm w-36 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={!!w}
                          onChange={() => toggleDay(day)}
                          className="rounded border-slate-300"
                        />
                        <span className="capitalize">{dayName(day)}</span>
                      </label>
                      {w && (
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-xs text-slate-400">{t.bkFrom}</span>
                          <Input
                            type="time"
                            value={w.start}
                            onChange={(e) => setTime(day, "start", e.target.value)}
                            className="!w-28"
                          />
                          <span className="text-xs text-slate-400">{t.bkTo}</span>
                          <Input
                            type="time"
                            value={w.end}
                            onChange={(e) => setTime(day, "end", e.target.value)}
                            className="!w-28"
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            <ErrorNote message={error} />
            <div className="flex items-center justify-between pt-1">
              <button
                onClick={() => setStep(2)}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                ← {t.obBack}
              </button>
              <Button
                onClick={async () => {
                  if (await saveBooking()) setStep(4);
                }}
                disabled={busy}
              >
                {busy ? t.loading : t.obFinish}
              </Button>
            </div>
          </Card>
        )}

        {step === 4 && (
          <Card className="p-8 text-center space-y-4">
            <span className="inline-flex h-14 w-14 rounded-full bg-emerald-100 text-emerald-600 items-center justify-center text-2xl">
              ✓
            </span>
            <h2 className="text-xl font-bold">
              {profile.is_visible ? t.obDoneT : t.mkProfileSaved}
            </h2>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              {profile.is_visible ? t.obDoneB : t.obDoneHidden}
            </p>
            <Button onClick={() => router.push("/dashboard?welcome=1")}>{t.obGoDash}</Button>
          </Card>
        )}
      </div>
    </div>
  );
}
