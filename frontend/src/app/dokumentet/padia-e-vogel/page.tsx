"use client";

// Public small-claims lawsuit wizard (XK only): guided questions -> formal
// lawsuit PDF (LPK arts. 484-491, <= 500 EUR) + court fee (UA 03/2025) +
// competent Basic Court by municipality. Document tool, not legal advice.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import { Button, Card, ErrorNote, Input, Label, Spinner, Textarea } from "@/components/ui";
import { IconDoc } from "@/components/icons";

interface ScField {
  key: string;
  type: string;
  label: Record<string, string>;
}

interface ScMeta {
  limit_eur: number;
  municipalities: string[];
  courts: Record<string, { seat: string; branch: string | null }>;
  fields: ScField[];
  legal_basis: string[];
}

const STEP_FIELDS: string[][] = [
  ["claim_amount", "claim_basis"],
  ["sender_name", "sender_address", "sender_phone", "defendant_name", "defendant_address"],
  ["evidence"],
];

export default function SmallClaimPage() {
  const { t, locale } = useI18n();
  const [meta, setMeta] = useState<ScMeta | null>(null);
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({});
  const [city, setCity] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    fetch("/api/public/tools/small-claims/meta")
      .then((res) => (res.ok ? res.json() : null))
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  const loc = (m: Record<string, string>) => m[locale] || m.sq || "";
  const fieldsByKey = useMemo(() => {
    const map: Record<string, ScField> = {};
    for (const f of meta?.fields || []) map[f.key] = f;
    return map;
  }, [meta]);

  const amount = parseFloat((values.claim_amount || "").replace(",", "."));
  const amountTooHigh = !Number.isNaN(amount) && meta != null && amount > meta.limit_eur;
  const fee = useMemo(() => {
    // UA 03/2025 civil band 0-5000 EUR = 60 EUR; small claims are always <= 500.
    return Number.isNaN(amount) || amount <= 0 ? null : 60;
  }, [amount]);

  const stepDone = (i: number) =>
    STEP_FIELDS[i].every((k) => (values[k] || "").trim().length > 0) &&
    !(i === 0 && (amountTooHigh || Number.isNaN(amount) || amount <= 0)) &&
    !(i === 2 && !city);

  async function generate() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/public/tools/small-claims/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values, city }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || t.error);
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "padia-vlere-vogel-avokatim.pdf";
      a.click();
      URL.revokeObjectURL(url);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  const renderField = (key: string) => {
    const f = fieldsByKey[key];
    if (!f) return null;
    return (
      <div key={key}>
        <Label>{loc(f.label)}</Label>
        {f.type === "textarea" ? (
          <Textarea
            rows={4}
            value={values[key] || ""}
            onChange={(e) => setValues({ ...values, [key]: e.target.value })}
          />
        ) : (
          <Input
            value={values[key] || ""}
            onChange={(e) => setValues({ ...values, [key]: e.target.value })}
          />
        )}
      </div>
    );
  };

  const stepTitles = [t.scStepCase, t.scStepParties, t.scStepEvidence];

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <IconDoc className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.scTitle}</h1>
        </div>
        <p className="text-sm text-slate-600">{t.scIntro}</p>

        {meta === null ? (
          <Spinner />
        ) : (
          <Card className="p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-semibold">
              {stepTitles.map((title, i) => (
                <span
                  key={title}
                  className={`rounded-full px-2.5 py-1 ${
                    i === step
                      ? "bg-indigo-600 text-white"
                      : i < step
                        ? "bg-indigo-100 text-indigo-700"
                        : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {i + 1}. {title}
                </span>
              ))}
            </div>

            <div className="space-y-3">
              {STEP_FIELDS[step].map(renderField)}
              {step === 0 && amountTooHigh && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 space-y-1.5">
                  <p className="text-xs text-amber-800">⚠ {t.scAmountHigh}</p>
                  <Link
                    href="/posto-rastin"
                    className="block text-xs font-semibold text-indigo-600 hover:underline"
                  >
                    {t.scFindLawyer} →
                  </Link>
                </div>
              )}
              {step === 2 && (
                <div>
                  <Label>{t.scCity}</Label>
                  <select
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="">—</option>
                    {meta.municipalities.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {step === 2 && city && fee != null && (
                <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-3 text-sm space-y-1">
                  <p>
                    <span className="font-semibold">{t.scCourt}:</span>{" "}
                    Gjykata Themelore — {meta.courts[city]?.seat || city}
                    {meta.courts[city]?.branch
                      ? ` (${t.scBranch}: ${meta.courts[city].branch})`
                      : ""}
                  </p>
                  <p>
                    <span className="font-semibold">{t.scFee}:</span> {fee.toFixed(2)} €
                  </p>
                  <p className="text-xs text-slate-500">{meta.legal_basis.join(" · ")}</p>
                </div>
              )}
            </div>

            <ErrorNote message={error} />

            <div className="flex items-center gap-2">
              {step > 0 && (
                <Button type="button" variant="secondary" onClick={() => setStep(step - 1)}>
                  ← {t.scBack}
                </Button>
              )}
              {step < 2 ? (
                <Button
                  type="button"
                  className="flex-1"
                  disabled={!stepDone(step)}
                  onClick={() => setStep(step + 1)}
                >
                  {t.scNext} →
                </Button>
              ) : (
                <Button
                  type="button"
                  className="flex-1"
                  disabled={busy || !stepDone(2)}
                  onClick={generate}
                >
                  {busy ? t.loading : `⬇ ${t.scDownload}`}
                </Button>
              )}
            </div>

            {done && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 space-y-1.5">
                <p className="text-xs font-semibold text-emerald-800">{t.scWhere}</p>
                <p className="text-xs text-emerald-800">{t.scGuide}</p>
                <Link
                  href="/posto-rastin"
                  className="block text-xs font-semibold text-indigo-600 hover:underline"
                >
                  {t.scFindLawyer} →
                </Link>
              </div>
            )}
          </Card>
        )}

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.scDisclaimer}</p>
      </main>
    </PublicShell>
  );
}
