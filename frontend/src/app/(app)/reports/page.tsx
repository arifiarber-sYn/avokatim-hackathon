"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Card, Spinner } from "@/components/ui";

interface Analytics {
  utilization: { billable_hours_mtd: number; target_monthly: number; pct: number | null };
  realization: { worked_hours_90d: number; billed_hours_90d: number; pct: number | null };
  collection: { issued_180d: number; paid_180d: number; pct: number | null };
  intake_funnel: {
    total: number;
    accepted: number;
    declined: number;
    pending: number;
    conversion_pct: number | null;
    by_source: { source: string; total: number; accepted: number }[];
  };
  profitability_by_area: {
    practice_area: string;
    hours: number;
    worked_value: number;
    billed_value: number;
  }[];
  by_lawyer: {
    user_id: string;
    full_name: string;
    role: string;
    open_matters: number;
    billable_hours_mtd: number;
    target_monthly: number;
    utilization_pct: number | null;
  }[];
}

function RateCard({
  title,
  hint,
  pct,
  detail,
  goodAbove,
  noData,
}: {
  title: string;
  hint: string;
  pct: number | null;
  detail: string;
  goodAbove: number;
  noData: string;
}) {
  const color =
    pct === null
      ? "text-slate-400"
      : pct >= goodAbove
        ? "text-emerald-600"
        : pct >= goodAbove * 0.7
          ? "text-amber-600"
          : "text-red-600";
  const barColor =
    pct === null
      ? "bg-slate-300"
      : pct >= goodAbove
        ? "bg-emerald-500"
        : pct >= goodAbove * 0.7
          ? "bg-amber-500"
          : "bg-red-500";
  return (
    <Card className="p-5">
      <h2 className="font-semibold">{title}</h2>
      <p className="text-xs text-slate-500 mt-0.5">{hint}</p>
      {pct === null ? (
        <p className="text-sm text-slate-400 mt-4">{noData}</p>
      ) : (
        <>
          <p className={`text-3xl font-bold mt-3 ${color}`}>{pct}%</p>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full rounded-full ${barColor}`}
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-2">{detail}</p>
        </>
      )}
    </Card>
  );
}

export default function ReportsPage() {
  const { t } = useI18n();
  const [data, setData] = useState<Analytics | null>(null);

  useEffect(() => {
    apiGet<Analytics>("/reports/analytics").then(setData).catch(() => {});
  }, []);

  if (!data) return <Spinner />;

  const dict = t as unknown as Record<string, string>;
  const sourceLabel = (s: string) =>
    s === "phone" ? t.phoneSource : dict[s] || s;
  const areaLabel = (a: string) => dict[a] || a;

  const funnel = data.intake_funnel;
  const maxBilled = Math.max(...data.profitability_by_area.map((p) => p.billed_value), 1);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.analytics}</h1>

      <div className="grid md:grid-cols-3 gap-4">
        <RateCard
          title={t.utilization}
          hint={t.utilizationHint}
          pct={data.utilization.pct}
          detail={`${data.utilization.billable_hours_mtd} / ${data.utilization.target_monthly} ${t.hoursUnit} (${t.monthlyTarget})`}
          goodAbove={70}
          noData={t.noDataYet}
        />
        <RateCard
          title={t.realization}
          hint={t.realizationHint}
          pct={data.realization.pct}
          detail={`${data.realization.billed_hours_90d} / ${data.realization.worked_hours_90d} ${t.hoursUnit}`}
          goodAbove={85}
          noData={t.noDataYet}
        />
        <RateCard
          title={t.collectionRate}
          hint={t.collectionHint}
          pct={data.collection.pct}
          detail={`€${data.collection.paid_180d.toFixed(2)} / €${data.collection.issued_180d.toFixed(2)}`}
          goodAbove={90}
          noData={t.noDataYet}
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <h2 className="font-semibold mb-4">{t.intakeFunnel}</h2>
          {funnel.total === 0 ? (
            <p className="text-sm text-slate-400">{t.noDataYet}</p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-baseline gap-4">
                <div>
                  <p className="text-3xl font-bold">
                    {funnel.conversion_pct === null ? "—" : `${funnel.conversion_pct}%`}
                  </p>
                  <p className="text-xs text-slate-500">{t.conversionRate}</p>
                </div>
                <div className="flex gap-4 text-sm text-slate-600">
                  <span>
                    <span className="font-semibold text-emerald-600">{funnel.accepted}</span>{" "}
                    {t.acceptedCount}
                  </span>
                  <span>
                    <span className="font-semibold text-red-600">{funnel.declined}</span>{" "}
                    {t.declinedCount}
                  </span>
                  <span>
                    <span className="font-semibold text-amber-600">{funnel.pending}</span>{" "}
                    {t.pendingCount}
                  </span>
                </div>
              </div>
              {funnel.by_source.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-slate-500 mb-2">{t.bySource}</p>
                  <div className="space-y-2">
                    {funnel.by_source.map((s) => (
                      <div key={s.source} className="flex items-center gap-3">
                        <span className="text-sm w-32 shrink-0 text-slate-600">
                          {sourceLabel(s.source)}
                        </span>
                        <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden flex">
                          <div
                            className="h-full bg-emerald-500"
                            style={{ width: `${(s.accepted / funnel.total) * 100}%` }}
                          />
                          <div
                            className="h-full bg-slate-300"
                            style={{ width: `${((s.total - s.accepted) / funnel.total) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500 tabular-nums w-14 text-right">
                          {s.accepted}/{s.total}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        <Card className="p-5">
          <h2 className="font-semibold mb-4">{t.profitabilityByArea}</h2>
          {data.profitability_by_area.length === 0 ? (
            <p className="text-sm text-slate-400">{t.noDataYet}</p>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[480px]">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                  <th className="pb-2 font-medium">{t.practiceArea}</th>
                  <th className="pb-2 font-medium text-right">{t.hoursUnit}</th>
                  <th className="pb-2 font-medium text-right">{t.workedValue}</th>
                  <th className="pb-2 font-medium text-right">{t.billedValue}</th>
                  <th className="pb-2 w-24" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {data.profitability_by_area.map((p) => (
                  <tr key={p.practice_area}>
                    <td className="py-2">{areaLabel(p.practice_area)}</td>
                    <td className="py-2 text-right tabular-nums">{p.hours}</td>
                    <td className="py-2 text-right tabular-nums">€{p.worked_value.toFixed(0)}</td>
                    <td className="py-2 text-right tabular-nums font-medium">
                      €{p.billed_value.toFixed(0)}
                    </td>
                    <td className="py-2 pl-3">
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${(p.billed_value / maxBilled) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </Card>
      </div>

      {data.by_lawyer.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold mb-4">{t.byLawyer}</h2>
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[560px]">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                <th className="pb-2 font-medium">{t.name}</th>
                <th className="pb-2 font-medium">{t.roleLabel}</th>
                <th className="pb-2 font-medium text-right">{t.openMatters}</th>
                <th className="pb-2 font-medium text-right">{t.hoursThisMonth}</th>
                <th className="pb-2 font-medium text-right">{t.utilization}</th>
                <th className="pb-2 w-24" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {data.by_lawyer.map((l) => {
                const roleKey = `role${l.role.charAt(0).toUpperCase()}${l.role.slice(1)}`;
                return (
                  <tr key={l.user_id}>
                    <td className="py-2 font-medium">{l.full_name}</td>
                    <td className="py-2 text-xs text-slate-500">{dict[roleKey] || l.role}</td>
                    <td className="py-2 text-right tabular-nums">{l.open_matters}</td>
                    <td className="py-2 text-right tabular-nums">
                      {l.billable_hours_mtd} / {l.target_monthly}
                    </td>
                    <td className="py-2 text-right tabular-nums">
                      {l.utilization_pct === null ? "—" : `${l.utilization_pct}%`}
                    </td>
                    <td className="py-2 pl-3">
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            (l.utilization_pct ?? 0) >= 70
                              ? "bg-emerald-500"
                              : (l.utilization_pct ?? 0) >= 49
                                ? "bg-amber-500"
                                : "bg-indigo-400"
                          }`}
                          style={{ width: `${Math.min(l.utilization_pct ?? 0, 100)}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        </Card>
      )}
    </div>
  );
}
