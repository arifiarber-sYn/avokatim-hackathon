"use client";

// Public legal-deadline calculator (no account needed) over the existing
// data-driven deadline engine. Information, not legal advice.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import { Button, Card, ErrorNote, Input, Label, Select, Spinner } from "@/components/ui";
import { IconCalendar } from "@/components/icons";

interface PublicRule {
  id: string;
  jurisdiction: string;
  code: string;
  name: Record<string, string>;
  legal_basis: string | null;
  practice_area: string | null;
  days: number;
  day_type: string;
}

interface CalcResult {
  due_date: string;
  days: number;
  day_type: string;
  legal_basis: string | null;
}

export default function DeadlineCalcPage() {
  const { t, locale } = useI18n();
  const [rules, setRules] = useState<PublicRule[] | null>(null);
  const [ruleId, setRuleId] = useState("");
  const [trigger, setTrigger] = useState("");
  const [result, setResult] = useState<CalcResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/public/tools/deadline-rules")
      .then((res) => res.json())
      .then(setRules)
      .catch(() => setRules([]));
  }, []);

  const ruleName = useMemo(
    () => (rule: PublicRule) => rule.name[locale] || rule.name.sq || rule.code,
    [locale]
  );

  async function calc(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/public/tools/deadline-calc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule_id: ruleId, trigger_date: trigger }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || t.error);
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  const selected = rules?.find((r) => r.id === ruleId);

  // The deadlines people actually search for (appeals + answer to claim);
  // one tap prefills the procedure and jumps to the date field
  const POPULAR_CODES = [
    "civil.appeal_judgment",
    "criminal.appeal_judgment",
    "civil.answer_to_claim",
    "administrative.appeal_decision",
    "labor.protection_claim",
  ];
  const popular = POPULAR_CODES
    .map((code) => rules?.find((r) => r.code === code))
    .filter((r): r is PublicRule => Boolean(r));

  function pickPopular(rule: PublicRule) {
    setRuleId(rule.id);
    setResult(null);
    document.getElementById("dc-trigger-date")?.focus();
  }

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <IconCalendar className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.dcTitle}</h1>
        </div>

        <PageIntro k="afatet" title={t.dcIntroT} body={t.dcIntro} />

        {rules !== null && popular.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold text-slate-500">{t.dcPopular}</p>
            <div className="flex flex-wrap gap-1.5">
              {popular.map((rule) => (
                <button
                  key={rule.id}
                  type="button"
                  onClick={() => pickPopular(rule)}
                  className={`text-xs rounded-full px-3 py-1.5 border transition ${
                    ruleId === rule.id
                      ? "bg-indigo-600 border-indigo-600 text-white"
                      : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-700"
                  }`}
                >
                  {ruleName(rule)} · {rule.days} {t.dcDaysShort}
                </button>
              ))}
            </div>
          </div>
        )}

        {rules === null ? (
          <Spinner />
        ) : (
          <Card className="p-5 space-y-4">
            <form onSubmit={calc} className="space-y-4">
              <div>
                <Label>{t.dcRule}</Label>
                <Select value={ruleId} onChange={(e) => { setRuleId(e.target.value); setResult(null); }} required>
                  <option value="">—</option>
                  {rules.map((rule) => (
                    <option key={rule.id} value={rule.id}>
                      {ruleName(rule)}
                      {rule.legal_basis ? ` (${rule.legal_basis})` : ""}
                    </option>
                  ))}
                </Select>
                {selected && (
                  <p className="text-xs text-slate-500 mt-1">
                    {selected.days}{" "}
                    {selected.day_type === "business" ? t.dcDaysBus : t.dcDaysCal}
                  </p>
                )}
              </div>
              <div>
                <Label>{t.dcTrigger}</Label>
                <Input
                  id="dc-trigger-date"
                  type="date"
                  value={trigger}
                  onChange={(e) => { setTrigger(e.target.value); setResult(null); }}
                  required
                />
                <p className="text-xs text-slate-400 mt-1">{t.dcTriggerHint}</p>
              </div>
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy || !ruleId || !trigger} className="w-full">
                {busy ? t.loading : t.dcCalc}
              </Button>
            </form>

            {result && (
              <div className="rounded-xl bg-indigo-50 border border-indigo-200 p-4 space-y-1">
                <p className="text-sm text-indigo-700 font-semibold">{t.dcResult}</p>
                <p className="text-2xl font-extrabold text-indigo-900">
                  {new Date(result.due_date + "T00:00:00").toLocaleDateString(undefined, {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </p>
                <p className="text-xs text-indigo-700">
                  {result.days} {result.day_type === "business" ? t.dcDaysBus : t.dcDaysCal}
                  {result.legal_basis ? ` · ${t.dcBasis}: ${result.legal_basis}` : ""}
                </p>
              </div>
            )}
          </Card>
        )}

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.dcDisclaimer}</p>

        <Link
          href="/posto-rastin"
          className="block text-center text-sm font-medium text-indigo-600 hover:underline"
        >
          {t.dcAskLawyer} →
        </Link>
      </main>
    </PublicShell>
  );
}
