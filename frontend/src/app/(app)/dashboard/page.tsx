"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import BookingsPanel from "@/components/bookings-panel";
import { BriefingCard } from "@/components/briefing-card";
import { Task } from "@/lib/types";
import { Badge, Card, SkeletonCards } from "@/components/ui";

interface AgendaItem {
  id: string;
  matter_id: string;
  matter_reference: string;
  matter_title: string;
  kind: string;
  title: string;
  due_at: string;
  legal_basis: string | null;
}

interface TrendPoint {
  month: string;
  hours: number;
  billed: number;
}

interface Dashboard {
  matters_by_status: Record<string, number>;
  deadlines_next_7_days: number;
  deadlines_overdue: number;
  intakes_pending: number;
  hours_this_month: number;
  unpaid_invoices_total: number;
  today_agenda: AgendaItem[];
  ar_aging: Record<string, number>;
  monthly_trend: TrendPoint[];
  onboarding?: { has_matter: boolean; has_document: boolean; has_assistant: boolean };
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

const KIND_STYLES: Record<string, string> = {
  hearing: "bg-purple-100 text-purple-800",
  deadline: "bg-amber-100 text-amber-800",
  meeting: "bg-blue-100 text-blue-800",
};

function MiniBarChart({
  title,
  points,
  format,
  barClass,
}: {
  title: string;
  points: { label: string; value: number }[];
  format: (v: number) => string;
  barClass: string;
}) {
  const max = Math.max(...points.map((p) => p.value), 1);
  return (
    <div className="flex-1 min-w-0">
      <p className="text-xs font-medium text-slate-500 mb-2">{title}</p>
      <div className="flex items-end gap-2 h-28">
        {points.map((p) => (
          <div key={p.label} className="flex-1 flex flex-col items-center justify-end gap-1 min-w-0">
            <span className="text-[10px] text-slate-600 whitespace-nowrap">
              {p.value > 0 ? format(p.value) : ""}
            </span>
            <div
              className={`w-full rounded-t ${barClass}`}
              style={{ height: `${Math.max((p.value / max) * 88, p.value > 0 ? 4 : 1)}px` }}
            />
            <span className="text-[10px] text-slate-400">{p.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Dismissible "what's new" showcase — feature discovery for tools that would
 * otherwise stay buried (versioned key: reappears only when the list changes). */
function WhatsNewCard() {
  const { t } = useI18n();
  // Bumped for the D-054 wave — the card reappears once for everyone
  const storageKey = "avokatim:whatsnew:2026-08";
  const [open, setOpen] = useState<boolean | null>(null);

  useEffect(() => {
    try {
      setOpen(localStorage.getItem(storageKey) !== "1");
    } catch {
      setOpen(true);
    }
  }, []);

  if (!open) return null;

  function dismiss() {
    setOpen(false);
    try {
      localStorage.setItem(storageKey, "1");
    } catch {}
  }

  return (
    <Card className="p-5 border-violet-200 bg-gradient-to-br from-violet-50/70 to-white">
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-semibold text-violet-900 flex items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-wider bg-violet-600 text-white rounded-full px-2 py-0.5">
            {t.wnBadge}
          </span>
          {t.wnTitle}
        </h2>
        <button
          onClick={dismiss}
          className="text-slate-400 hover:text-slate-600 text-lg leading-none shrink-0 p-2 -m-2"
          aria-label={t.introHide}
        >
          ×
        </button>
      </div>
      <div className="grid sm:grid-cols-2 gap-4 mt-3">
        <div className="text-sm space-y-1.5">
          <p className="text-slate-700">{t.wnAgent}</p>
          <Link href="/assistant" className="inline-block py-1.5 font-semibold text-violet-700 hover:underline">
            {t.wnAgentCta} →
          </Link>
        </div>
        <div className="text-sm space-y-1.5">
          <p className="text-slate-700">{t.wnBriefing}</p>
          <Link href="/settings#grp-njoftimet" className="inline-block py-1.5 font-semibold text-violet-700 hover:underline">
            {t.wnBriefingCta} →
          </Link>
        </div>
        <div className="text-sm space-y-1.5">
          <p className="text-slate-700">{t.wnPasskey}</p>
          <Link href="/settings#grp-siguria" className="inline-block py-1.5 font-semibold text-violet-700 hover:underline">
            {t.wnPasskeyCta} →
          </Link>
        </div>
        <div className="text-sm space-y-1.5">
          <p className="text-slate-700">{t.wnUx}</p>
        </div>
      </div>
    </Card>
  );
}

type DlSuggestion = {
  id: string;
  matter_id: string;
  matter_reference?: string | null;
  title: string;
};

type EmailSug = {
  id: string;
  matter_id: string;
  matter_reference?: string | null;
  matter_title?: string | null;
  sender: string;
  subject: string;
  contact_name?: string | null;
};

export default function DashboardPage() {
  const { t, locale } = useI18n();
  const [data, setData] = useState<Dashboard | null>(null);
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [welcome, setWelcome] = useState(false);
  const [profileVisible, setProfileVisible] = useState<boolean | null>(null);
  const [profession, setProfession] = useState<string>("lawyer");
  const [timeSuggestions, setTimeSuggestions] = useState(0);
  const [dlSuggestions, setDlSuggestions] = useState<DlSuggestion[]>([]);
  const [emailSugs, setEmailSugs] = useState<EmailSug[]>([]);

  const loadEmailSugs = useCallback(() => {
    apiGet<EmailSug[]>("/email-suggestions").then(setEmailSugs).catch(() => {});
  }, []);

  const loadTasks = useCallback(() => {
    apiGet<Task[]>("/tasks?mine=true&open_only=true").then(setTasks).catch(() => {});
  }, []);

  useEffect(() => {
    apiGet<Dashboard>("/reports/dashboard").then(setData).catch(() => {});
    apiGet<Deadline[]>("/deadlines/upcoming?days=30").then(setDeadlines).catch(() => {});
    apiGet<{ is_visible: boolean }>("/marketplace/profile")
      .then((p) => setProfileVisible(p.is_visible))
      .catch(() => {});
    apiGet<{ tenant_profession?: string }>("/auth/me")
      .then((m) => setProfession(m.tenant_profession || "lawyer"))
      .catch(() => {});
    apiGet<unknown[]>("/time-suggestions")
      .then((s) => setTimeSuggestions(s.length))
      .catch(() => {});
    apiGet<DlSuggestion[]>("/deadline-suggestions")
      .then(setDlSuggestions)
      .catch(() => {});
    loadEmailSugs();
    loadTasks();
    if (
      new URLSearchParams(window.location.search).get("welcome") &&
      !localStorage.getItem("avokatim_welcome_done")
    ) {
      setWelcome(true);
    }
  }, [loadTasks, loadEmailSugs]);

  async function acceptEmailSug(id: string) {
    await apiPost(`/email-suggestions/${id}/accept`);
    loadEmailSugs();
  }

  async function dismissEmailSug(id: string) {
    await apiPost(`/email-suggestions/${id}/dismiss`);
    loadEmailSugs();
  }

  async function completeTask(task: Task) {
    await apiPatch(`/tasks/${task.id}`, { status: "done" });
    loadTasks();
  }

  if (!data) return <SkeletonCards count={4} lines={3} />;

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

  const kindLabel = (kind: string) =>
    ((t as unknown as Record<string, string>)[kind] as string) || kind;

  const monthLabel = (ym: string) => {
    const [y, m] = ym.split("-").map(Number);
    return new Date(y, m - 1, 1).toLocaleDateString(locale, { month: "short" });
  };

  const agingBuckets = [
    { key: "0_30", label: `0–30 ${t.agingDays}`, tone: "text-slate-700" },
    { key: "31_60", label: `31–60 ${t.agingDays}`, tone: "text-amber-600" },
    { key: "61_90", label: `61–90 ${t.agingDays}`, tone: "text-orange-600" },
    { key: "91_plus", label: t.agingOver90, tone: "text-red-600" },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.dashboard}</h1>

      <PageIntro k="dashboard" title={t.dashIntroT} body={t.dashIntro} />

      {/* Onboarding checklist (audit 2026-09-18, adv. #3): shown until the
          office has tried the three core actions */}
      {data.onboarding &&
        !(data.onboarding.has_matter && data.onboarding.has_document && data.onboarding.has_assistant) && (
        <Card className="p-5 border-indigo-200 bg-indigo-50/50">
          <h2 className="font-semibold text-indigo-900">{t.obcTitle}</h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {[
              { done: data.onboarding.has_matter, label: t.obcMatter, href: "/matters" },
              { done: data.onboarding.has_document, label: t.obcDocument, href: "/matters" },
              { done: data.onboarding.has_assistant, label: t.obcAssistant, href: "/assistant" },
            ].map((step) => (
              <Link
                key={step.label}
                href={step.href}
                className={`flex items-center gap-2 rounded-xl border px-3 py-2.5 text-sm transition ${
                  step.done
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                    : "border-indigo-200 bg-white text-indigo-900 hover:border-indigo-400"
                }`}
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
                    step.done ? "bg-emerald-600 text-white" : "border border-indigo-300 text-indigo-400"
                  }`}
                >
                  {step.done ? "✓" : ""}
                </span>
                {step.label}
              </Link>
            ))}
          </div>
        </Card>
      )}

      <BriefingCard />

      <WhatsNewCard />

      {/* Notary offices have no marketplace page, so their appointment
          requests from /noteret surface here on the dashboard */}
      {profession === "notary" && <BookingsPanel />}

      {timeSuggestions > 0 && (
        <Card className="p-5 border-amber-300 bg-amber-50/60">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="font-semibold text-amber-900">{t.tsDashTitle}</h2>
              <p className="text-sm text-amber-800 mt-1">
                {t.tsDashBody.replace("{n}", String(timeSuggestions))}
              </p>
            </div>
            <Link
              href="/billing"
              className="shrink-0 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2"
            >
              {t.tsDashCta}
            </Link>
          </div>
        </Card>
      )}

      {dlSuggestions.length > 0 && (
        <Card className="p-5 border-indigo-300 bg-indigo-50/60">
          <h2 className="font-semibold text-indigo-900">{t.dlsTitle}</h2>
          <p className="text-sm text-indigo-800 mt-1">
            {t.dlsDashBody.replace("{n}", String(dlSuggestions.length))}
          </p>
          <ul className="mt-2 space-y-1 text-sm">
            {dlSuggestions.slice(0, 4).map((s) => (
              <li key={s.id}>
                <Link
                  href={`/matters/${s.matter_id}`}
                  className="text-indigo-700 hover:underline"
                >
                  {s.matter_reference ? `${s.matter_reference} — ` : ""}
                  {s.title}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {emailSugs.length > 0 && (
        <Card className="p-5 border-sky-300 bg-sky-50/60">
          <h2 className="font-semibold text-sky-900">{t.emsTitle}</h2>
          <p className="text-sm text-sky-800 mt-1">
            {t.emsDashBody.replace("{n}", String(emailSugs.length))} · {t.emsHint}
          </p>
          <ul className="mt-2 space-y-2">
            {emailSugs.slice(0, 5).map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between gap-3 flex-wrap rounded-lg border border-sky-200 bg-white/70 px-3 py-2"
              >
                <div className="min-w-0 text-sm">
                  <p className="text-slate-800 truncate">
                    <span className="font-medium">{s.contact_name || s.sender}</span>
                    {s.subject ? ` — ${s.subject}` : ""}
                  </p>
                  <p className="text-xs text-slate-500">
                    {t.emsSuggested}:{" "}
                    <Link
                      href={`/matters/${s.matter_id}`}
                      className="text-sky-700 hover:underline"
                    >
                      {s.matter_reference} — {s.matter_title}
                    </Link>
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => acceptEmailSug(s.id)}
                    className="rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-3 py-1.5"
                  >
                    {t.emsAccept}
                  </button>
                  <button
                    onClick={() => dismissEmailSug(s.id)}
                    className="rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 text-xs font-semibold px-3 py-1.5"
                  >
                    {t.emsDismiss}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {profileVisible === false && profession !== "notary" && (
        <Card className="p-5 border-amber-300 bg-amber-50/60">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="font-semibold text-amber-900">{t.pubProfileNudgeT}</h2>
              <p className="text-sm text-amber-800 mt-1">{t.pubProfileNudge}</p>
            </div>
            <Link
              href="/settings#public-profile"
              className="shrink-0 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2"
            >
              {t.pubProfileNudgeCta}
            </Link>
          </div>
        </Card>
      )}

      {welcome && (
        <Card className="p-5 border-indigo-300 bg-indigo-50/50">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="font-semibold">{t.welcomeTitle}</h2>
              <p className="text-sm text-slate-600 mt-1">{t.welcomeSubtitle}</p>
            </div>
            <button
              onClick={() => {
                localStorage.setItem("avokatim_welcome_done", "1");
                setWelcome(false);
              }}
              className="text-slate-400 hover:text-slate-600 text-lg leading-none p-2 -m-2"
            >
              ✕
            </button>
          </div>
          <ol className="mt-3 space-y-2 text-sm list-decimal list-inside">
            <li>
              <Link href="/settings" className="text-indigo-700 hover:underline">
                {t.welcomeStepTeam}
              </Link>
            </li>
            <li>
              <Link href="/settings" className="text-indigo-700 hover:underline">
                {t.welcomeStepImport}
              </Link>
            </li>
            <li>
              <Link href="/settings" className="text-indigo-700 hover:underline">
                {t.welcomeStepLogo}
              </Link>
            </li>
            <li>
              <Link href="/matters" className="text-indigo-700 hover:underline">
                {t.welcomeStepMatter}
              </Link>
            </li>
          </ol>
        </Card>
      )}

      <Card className="p-5 border-indigo-200">
        <h2 className="font-semibold mb-3">
          {t.todayAgenda}
          <span className="ml-2 text-sm font-normal text-slate-400">
            {new Date().toLocaleDateString(locale, {
              weekday: "long",
              day: "numeric",
              month: "long",
            })}
          </span>
        </h2>
        {data.today_agenda.length === 0 ? (
          <p className="text-sm text-slate-500">{t.noAgendaToday}</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {data.today_agenda.map((a) => (
              <Link
                key={a.id}
                href={`/matters/${a.matter_id}`}
                className="flex items-center gap-3 py-2.5 hover:bg-slate-50 px-2 -mx-2 rounded"
              >
                <span className="text-sm font-semibold tabular-nums w-12">
                  {new Date(a.due_at).toLocaleTimeString(locale, {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                <span
                  className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    KIND_STYLES[a.kind] || "bg-slate-100 text-slate-600"
                  }`}
                >
                  {kindLabel(a.kind)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{a.title}</p>
                  <p className="text-xs text-slate-500 truncate">
                    {a.matter_reference} · {a.matter_title}
                    {a.legal_basis ? ` · ${a.legal_basis}` : ""}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      {tasks.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold mb-3">
            {t.myTasks}
            <span className="ml-2 text-sm font-normal text-slate-400">{tasks.length}</span>
          </h2>
          <div className="divide-y divide-slate-100">
            {tasks.slice(0, 8).map((task) => {
              const overdue = task.due_date && new Date(task.due_date) < new Date();
              return (
                <div key={task.id} className="flex items-center gap-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    className="cursor-pointer"
                    checked={false}
                    onChange={() => completeTask(task)}
                  />
                  {task.matter_id ? (
                    <Link
                      href={`/matters/${task.matter_id}`}
                      className="flex-1 min-w-0 truncate font-medium hover:text-indigo-700"
                    >
                      {task.title}
                    </Link>
                  ) : (
                    <span className="flex-1 min-w-0 truncate font-medium">{task.title}</span>
                  )}
                  {(task.priority === "high" || task.priority === "urgent") && (
                    <Badge
                      status="overdue"
                      label={task.priority === "urgent" ? t.priorityUrgent : t.priorityHigh}
                    />
                  )}
                  {task.due_date && (
                    <span className={`text-xs tabular-nums ${overdue ? "text-red-600 font-semibold" : "text-slate-500"}`}>
                      {new Date(task.due_date).toLocaleDateString()}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

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

      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="p-5 lg:col-span-2">
          <h2 className="font-semibold mb-4">{t.monthlyTrend}</h2>
          <div className="flex flex-col sm:flex-row gap-6 sm:gap-8">
            <MiniBarChart
              title={t.workedHours}
              points={data.monthly_trend.map((p) => ({
                label: monthLabel(p.month),
                value: p.hours,
              }))}
              format={(v) => `${v}h`}
              barClass="bg-indigo-500"
            />
            <MiniBarChart
              title={t.billedRevenue}
              points={data.monthly_trend.map((p) => ({
                label: monthLabel(p.month),
                value: p.billed,
              }))}
              format={(v) => `€${v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0)}`}
              barClass="bg-emerald-500"
            />
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="font-semibold mb-4">{t.arAging}</h2>
          <div className="space-y-3">
            {agingBuckets.map((b) => {
              const value = data.ar_aging[b.key] || 0;
              const total = Object.values(data.ar_aging).reduce((s, v) => s + v, 0) || 1;
              return (
                <div key={b.key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">{b.label}</span>
                    <span className={`font-medium tabular-nums ${b.tone}`}>
                      €{value.toFixed(2)}
                    </span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-400 rounded-full"
                      style={{ width: `${(value / total) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
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
