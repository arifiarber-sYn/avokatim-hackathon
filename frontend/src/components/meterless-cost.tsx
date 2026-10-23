"use client";

/**
 * Meterless usage badge (Open Agent 2026, B2).
 *
 * Reads GET /hackathon/usage — the aggregate of data/evidence/usage.jsonl that
 * the Meterless adapter writes on every local-model call — and shows what the
 * answers actually cost. With Nightshift on this machine the marginal price is
 * zero; the badge still shows the tokens, because "free" only means something
 * when the work behind it is visible.
 *
 * Renders nothing when the log is empty (production, hackathon_mode off), so
 * the ordinary assistant page is unchanged.
 */
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface UsageSummary {
  calls: number;
  tokens_in: number;
  tokens_out: number;
  tokens_total: number;
  cost_usd: number;
  ms_avg: number;
  meterless_configured: boolean;
}

const num = (n: number) => n.toLocaleString("de-DE");

export default function MeterlessCost() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);

  useEffect(() => {
    apiGet<UsageSummary>("/hackathon/usage?last=1").then(setUsage).catch(() => {});
  }, []);

  if (!usage || !usage.calls) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500">
      <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-emerald-700">
        Meterless · {num(usage.calls)} thirrje
      </span>
      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5">
        {num(usage.tokens_total)} token
      </span>
      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5">
        kosto ${usage.cost_usd.toFixed(4)}
      </span>
      {usage.ms_avg > 0 && (
        <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5">
          {num(usage.ms_avg)} ms mesatarisht
        </span>
      )}
      <span
        className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-indigo-700"
        title="Modeli lokal i Meterless: përmbajtja e klientit nuk del nga makina."
      >
        dokumentet nuk dolën nga makina
      </span>
    </div>
  );
}
