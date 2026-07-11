"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet, getToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import { Deadline } from "@/lib/types";
import { Badge, Card, Spinner } from "@/components/ui";

export default function CalendarPage() {
  const { t } = useI18n();
  const [deadlines, setDeadlines] = useState<Deadline[] | null>(null);

  const load = () =>
    apiGet<Deadline[]>("/deadlines/upcoming?days=90").then(setDeadlines).catch(() => {});

  useEffect(() => {
    load();
  }, []);

  async function markDone(id: string) {
    await fetch(`/api/deadlines/${id}/status?new_status=done`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    load();
  }

  if (deadlines === null) return <Spinner />;

  const groups = new Map<string, Deadline[]>();
  for (const d of deadlines) {
    const key = new Date(d.due_at).toLocaleDateString(undefined, {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(d);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.calendar}</h1>
      <PageIntro k="calendar" title={t.calendarIntroT} body={t.calendarIntro} />
      {deadlines.length === 0 && <p className="text-sm text-slate-500">{t.noDeadlines}</p>}
      {[...groups.entries()].map(([day, items]) => (
        <div key={day}>
          <h2 className="text-sm font-semibold text-slate-500 mb-2">{day}</h2>
          <Card>
            <div className="divide-y divide-slate-100">
              {items.map((d) => {
                const overdue = new Date(d.due_at) < new Date();
                return (
                  <div key={d.id} className="flex justify-between items-center px-4 py-3 text-sm">
                    <div className="min-w-0">
                      <Link href={`/matters/${d.matter_id}`} className="font-medium hover:underline">
                        {d.title}
                      </Link>
                      <p className="text-xs text-slate-500">
                        {d.legal_basis || (t as Record<string, string>)[d.kind]}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {overdue && <Badge status="missed" label={t.overdue} />}
                      <Badge status={d.kind === "hearing" ? "sent" : "pending"} label={(t as Record<string, string>)[d.kind]} />
                      <button onClick={() => markDone(d.id)} className="text-xs text-emerald-600 hover:underline">
                        {t.markDone}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
}
