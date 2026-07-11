"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { LOCALES } from "@/lib/dictionaries";
import { PublicLawyer } from "@/lib/citizen";
import { Card, Input, Select, Spinner } from "@/components/ui";
import PublicShell from "@/components/public-shell";

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
                    <p className="font-semibold truncate">{lawyer.full_name}</p>
                    <p className="text-xs text-slate-500 truncate">{lawyer.firm_name}</p>
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
                <Link
                  href={`/posto-rastin?avokati=${lawyer.tenant_id}`}
                  className="inline-block text-sm font-medium text-indigo-600 hover:underline"
                >
                  {t.mkContactLawyer} →
                </Link>
              </Card>
            ))}
          </div>
        )}
      </main>
    </PublicShell>
  );
}
