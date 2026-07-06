"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Badge, Card, Spinner } from "@/components/ui";

interface Dashboard {
  matters_by_status: Record<string, number>;
  deadlines_next_7_days: number;
  deadlines_overdue: number;
  intakes_pending: number;
  hours_this_month: number;
  unpaid_invoices_total: number;
}

interface Deadline {
  id: string;
  matter_id: string;
  title: string;
  due_at: string;
  legal_basis: string | null;
  status: string;
  kind: string;
}

export default function DashboardPage() {
  const { t } = useI18n();
  const [data, setData] = useState<Dashboard | null>(null);
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);

  useEffect(() => {
    apiGet<Dashboard>("/reports/dashboard").then(setData).catch(() => {});
    apiGet<Deadline[]>("/deadlines/upcoming?days=30").then(setDeadlines).catch(() => {});
  }, []);

  if (!data) return <Spinner />;

  const stats = [
    { label: t.openMatters, value: data.matters_by_status.open || 0, href: "/matters" },
    {
      label: t.deadlines7d,
      value: data.deadlines_next_7_days,
      href: "/calendar",
      alert: data.deadlines_next_7_days > 0,
    },
    {
      label: t.overdue,
      value: data.deadlines_overdue,
      href: "/calendar",
      danger: data.deadlines_overdue > 0,
    },
    { label: t.pendingIntakes, value: data.intakes_pending, href: "/intake" },
    { label: t.hoursThisMonth, value: data.hours_this_month, href: "/billing" },
    {
      label: t.unpaidInvoices,
      value: `€${data.unpaid_invoices_total.toFixed(2)}`,
      href: "/billing",
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.dashboard}</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((s) => (
          <Link key={s.label} href={s.href}>
            <Card
              className={`p-4 hover:shadow-md transition-shadow ${
                s.danger ? "border-red-300 bg-red-50" : s.alert ? "border-amber-300" : ""
              }`}
            >
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="text-xs text-slate-500 mt-1">{s.label}</p>
            </Card>
          </Link>
        ))}
      </div>

      <Card className="p-5">
        <h2 className="font-semibold mb-4">{t.upcomingDeadlines}</h2>
        {deadlines.length === 0 ? (
          <p className="text-sm text-slate-500">{t.noDeadlines}</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {deadlines.map((d) => {
              const overdue = new Date(d.due_at) < new Date();
              return (
                <Link
                  key={d.id}
                  href={`/matters/${d.matter_id}`}
                  className="flex items-center justify-between py-3 hover:bg-slate-50 px-2 -mx-2 rounded"
                >
                  <div>
                    <p className="text-sm font-medium">{d.title}</p>
                    {d.legal_basis && (
                      <p className="text-xs text-slate-500">{d.legal_basis}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${overdue ? "text-red-600" : ""}`}>
                      {new Date(d.due_at).toLocaleDateString()}
                    </p>
                    <Badge status={d.status} />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
