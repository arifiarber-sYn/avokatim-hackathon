"use client";

// Public litigation cost calculator for the Kosovo host ("Sa kushton një
// proces gjyqësor?") over the data-driven UA 03/2025 court-fee table and
// the OAK lawyer tariff. Information, not legal advice. XK twin of the
// Prozesskostenrisiko section of /rvg.
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { clientCountry } from "@/lib/country";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import { Button, Card, ErrorNote, Input, Label, Select } from "@/components/ui";
import { IconScale } from "@/components/icons";

interface Track {
  code: string;
  name: Record<string, string>;
}

interface RiskLine {
  vv: string;
  rate: string | null;
  name: Record<string, string>;
  amount: string;
}

interface RiskInstance {
  code: string;
  name: Record<string, string>;
  court_note: string;
  court_fee: string;
  own_lawyer: { lines: RiskLine[]; net: string; vat: string; total: string };
  opponent_lawyer_total: string;
  total_if_lose: string;
  cumulative_if_lose: string;
}

interface RiskResult {
  value: string;
  legal_basis: string;
  court_fee_advance: string;
  instances: RiskInstance[];
  total_risk: string;
}

export default function KostojaPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [tracks, setTracks] = useState<Track[]>([]);
  const [track, setTrack] = useState("civil");
  const [value, setValue] = useState("");
  const [result, setResult] = useState<RiskResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (clientCountry() !== "XK") {
      router.replace("/");
      return;
    }
    fetch("/api/public/tools/process-cost")
      .then((res) => (res.ok ? res.json() : { tracks: [] }))
      .then((data) => setTracks(data.tracks || []))
      .catch(() => setTracks([]));
  }, [router]);

  const label = useMemo(
    () => (name: Record<string, string>) => name[locale] || name.sq || name.en,
    [locale]
  );

  async function calc(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/public/tools/process-cost", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value_eur: Number(value), track }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || t.error);
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <IconScale className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.kstTitle}</h1>
        </div>

        <PageIntro k="kostoja" title={t.kstTitle} body={t.kstIntro} />

        <Card className="p-5 space-y-4">
          <form onSubmit={calc} className="space-y-3">
            <div>
              <Label>{t.kstTrack}</Label>
              <Select value={track} onChange={(e) => { setTrack(e.target.value); setResult(null); }}>
                {(tracks.length
                  ? tracks
                  : [{ code: "civil", name: { sq: "Kontest civil" } }]
                ).map((tr) => (
                  <option key={tr.code} value={tr.code}>{label(tr.name)}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t.rvgValue}</Label>
              <Input
                type="number"
                min="1"
                step="1"
                value={value}
                onChange={(e) => { setValue(e.target.value); setResult(null); }}
                required
              />
            </div>
            <ErrorNote message={error} />
            <Button type="submit" disabled={busy || !value} className="w-full">
              {busy ? t.loading : t.pkrCalc}
            </Button>
          </form>

          {result && (
            <div className="space-y-3">
              {result.instances.map((inst) => (
                <div key={inst.code} className="rounded-xl border border-slate-200 p-4 space-y-1.5">
                  <p className="text-sm font-semibold text-slate-800">{label(inst.name)}</p>
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>
                      {t.pkrCourtFee}{" "}
                      <span className="text-slate-400">({inst.court_note})</span>
                    </span>
                    <span className="font-mono">{Number(inst.court_fee).toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>
                      {t.pkrOwnLawyer}{" "}
                      <span className="text-slate-400">
                        ({inst.own_lawyer.lines.map((l) => l.vv + (l.rate ? ` ${l.rate}` : "")).join(" + ")})
                      </span>
                    </span>
                    <span className="font-mono">{Number(inst.own_lawyer.total).toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>{t.pkrOppLawyer}</span>
                    <span className="font-mono">{Number(inst.opponent_lawyer_total).toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between text-sm font-semibold text-slate-800 border-t border-slate-100 pt-1.5">
                    <span>{t.pkrIfLose}</span>
                    <span className="font-mono">{Number(inst.total_if_lose).toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>{t.pkrCumulative}</span>
                    <span className="font-mono">{Number(inst.cumulative_if_lose).toFixed(2)} €</span>
                  </div>
                </div>
              ))}
              <div className="rounded-xl bg-indigo-50 border border-indigo-200 p-4 space-y-1.5">
                <div className="flex justify-between text-sm text-indigo-900">
                  <span>{t.kstAdvance}</span>
                  <span className="font-mono">{Number(result.court_fee_advance).toFixed(2)} €</span>
                </div>
                <div className="flex justify-between font-bold text-base text-indigo-900">
                  <span>{t.pkrTotalRisk}</span>
                  <span className="font-mono">{Number(result.total_risk).toFixed(2)} €</span>
                </div>
                <p className="text-xs text-indigo-700">{t.kstWinNote}</p>
                <p className="text-xs text-indigo-400">{result.legal_basis}</p>
              </div>
            </div>
          )}
        </Card>

        <p className="text-xs text-slate-400">{t.rvgDisclaimer}</p>
      </main>
    </PublicShell>
  );
}
