"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Badge, Button, Card, ErrorNote, Input, Spinner } from "@/components/ui";

interface TenantRow {
  id: string;
  name: string;
  kind: string;
  plan: string;
  status: string;
  seats_limit: number;
  seats_used: number;
  matters_count: number;
  trial_ends_at: string | null;
  plan_price_eur: number;
  billing_notes: string | null;
  created_at: string;
}

interface PlatformInvoiceRow {
  id: string;
  number: string;
  tenant_id: string;
  tenant_name: string;
  period_start: string;
  plan: string;
  seats: number;
  amount_eur: number;
  status: string;
  due_on: string;
  paid_on: string | null;
  payment_reference: string | null;
  overdue_days: number;
}

export default function PlatformPage() {
  const { t } = useI18n();
  const [tenants, setTenants] = useState<TenantRow[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<TenantRow[]>("/platform/tenants")
      .then(setTenants)
      .catch((err) => setError(err instanceof Error ? err.message : "error"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function act(id: string, action: "suspend" | "activate") {
    setError("");
    try {
      await apiPost(`/platform/tenants/${id}/${action}`, {});
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    }
  }

  async function update(id: string, patch: Record<string, unknown>) {
    setError("");
    try {
      await apiPatch(`/platform/tenants/${id}`, patch);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    }
  }

  if (tenants === null) return <Spinner />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.platform}</h1>
      <ErrorNote message={error} />
      <div className="space-y-3">
        {tenants.map((tn) => (
          <TenantCard key={tn.id} tenant={tn} onAct={act} onUpdate={update} />
        ))}
      </div>
      <VerificationsSection />
      <PlatformInvoicesSection />
      <FeedbackSection />
    </div>
  );
}

interface FeedbackRow {
  id: string;
  kind: string;
  name: string | null;
  email: string | null;
  message: string;
  status: string;
  handled_note: string | null;
  created_at: string;
}

function FeedbackSection() {
  const { t } = useI18n();
  const [tab, setTab] = useState<"new" | "handled">("new");
  const [rows, setRows] = useState<FeedbackRow[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    apiGet<FeedbackRow[]>(`/platform/feedback?status_filter=${tab}`)
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "error"));
  }, [tab]);
  useEffect(() => {
    load();
  }, [load]);

  async function handle(id: string) {
    const note = window.prompt(t.pfHandle) || null;
    setBusy(true);
    setError("");
    try {
      await apiPost(`/platform/feedback/${id}/handle`, { note });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    } finally {
      setBusy(false);
    }
  }

  const kindLabels: Record<string, string> = {
    ankese: t.ctKindAnkese,
    sugjerim: t.ctKindSugjerim,
    problem: t.ctKindProblem,
  };
  const kindTone: Record<string, string> = {
    ankese: "bg-red-100 text-red-800",
    sugjerim: "bg-indigo-100 text-indigo-800",
    problem: "bg-amber-100 text-amber-800",
  };

  return (
    <Card className="p-5 space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-lg font-semibold">{t.pfTitle}</h2>
        <div className="flex gap-1 text-sm">
          {(["new", "handled"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setTab(s)}
              className={`px-3 py-1 rounded-lg ${
                tab === s ? "bg-indigo-600 text-white" : "text-slate-500 hover:bg-slate-100"
              }`}
            >
              {s === "new" ? t.pfNew : t.pfHandledTab}
            </button>
          ))}
        </div>
      </div>
      <ErrorNote message={error} />
      {rows === null ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-500">{t.pfEmpty}</p>
      ) : (
        <div className="space-y-2">
          {rows.map((row) => (
            <div key={row.id} className="border border-slate-200 rounded-lg px-3 py-2.5 space-y-1.5">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                <span className={`inline-flex px-2 py-0.5 rounded-full font-medium ${kindTone[row.kind] || ""}`}>
                  {kindLabels[row.kind] || row.kind}
                </span>
                <span className="text-slate-500">
                  {new Date(row.created_at).toLocaleString()}
                </span>
                {row.name && <span className="text-slate-600 font-medium">{row.name}</span>}
                {row.email && <span className="text-slate-500">{row.email}</span>}
                {row.status === "new" && (
                  <Button
                    variant="secondary"
                    disabled={busy}
                    onClick={() => handle(row.id)}
                    className="ml-auto"
                  >
                    {t.pfHandle}
                  </Button>
                )}
              </div>
              <p className="text-sm text-slate-700 whitespace-pre-wrap">{row.message}</p>
              {row.handled_note && (
                <p className="text-xs text-slate-400 italic">{row.handled_note}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

interface VerificationRow {
  profile_id: string;
  lawyer_name: string;
  lawyer_email: string;
  tenant_name: string;
  oak_license_no: string | null;
  verification_status: string;
  verification_note: string | null;
  submitted_at: string;
}

function VerificationsSection() {
  const { t } = useI18n();
  const [rows, setRows] = useState<VerificationRow[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    apiGet<VerificationRow[]>("/platform/verifications")
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "error"));
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  async function decide(profileId: string, approve: boolean) {
    let note: string | null = null;
    if (!approve) {
      note = window.prompt(t.platRejectNote) || null;
      if (note === null) return;
    }
    setBusy(true);
    setError("");
    try {
      await apiPost(`/platform/verifications/${profileId}/decide`, { approve, note });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 space-y-3">
      <div>
        <h2 className="text-lg font-semibold">{t.platVerifTitle}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.platVerifHint}</p>
      </div>
      <ErrorNote message={error} />
      {rows === null ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-500">{t.platVerifEmpty}</p>
      ) : (
        <div className="space-y-2">
          {rows.map((row) => (
            <div
              key={row.profile_id}
              className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm border border-slate-200 rounded-lg px-3 py-2"
            >
              <span className="font-medium">{row.lawyer_name}</span>
              <span className="text-slate-500">{row.lawyer_email}</span>
              <span className="text-slate-500">{row.tenant_name}</span>
              <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-amber-100 text-amber-800">
                OAK {row.oak_license_no}
              </span>
              <span className="flex gap-2 ml-auto">
                <Button disabled={busy} onClick={() => decide(row.profile_id, true)}>
                  {t.platApprove}
                </Button>
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={() => decide(row.profile_id, false)}
                >
                  {t.platReject}
                </Button>
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function PlatformInvoicesSection() {
  const { t } = useI18n();
  const [invoices, setInvoices] = useState<PlatformInvoiceRow[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    apiGet<PlatformInvoiceRow[]>("/platform/invoices")
      .then(setInvoices)
      .catch((err) => setError(err instanceof Error ? err.message : "error"));
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await action();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    } finally {
      setBusy(false);
    }
  }

  const statusLabel = (s: string) =>
    s === "paid" ? t.subStatusPaid : s === "void" ? t.subStatusVoid : t.subStatusOpen;

  return (
    <Card className="p-5 space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-lg font-semibold">{t.platInvoicesTitle}</h2>
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => run(() => apiPost("/platform/invoices/generate", {}))}
        >
          {t.platGenerate}
        </Button>
      </div>
      <ErrorNote message={error} />
      {invoices === null ? (
        <Spinner />
      ) : invoices.length === 0 ? (
        <p className="text-sm text-slate-500">{t.subNoInvoices}</p>
      ) : (
        <div className="space-y-2">
          {invoices.map((inv) => (
            <div
              key={inv.id}
              className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm border border-slate-200 rounded-lg px-3 py-2"
            >
              <span className="font-mono">{inv.number}</span>
              <span className="font-medium">{inv.tenant_name}</span>
              <span className="text-slate-500">
                {new Date(inv.period_start).toLocaleDateString(undefined, { month: "2-digit", year: "numeric" })}
                {" · "}
                {inv.seats}p
              </span>
              <span>
                <b>{inv.amount_eur.toFixed(2)} €</b>
              </span>
              <span
                className={
                  inv.status === "paid"
                    ? "text-emerald-700"
                    : inv.status === "void"
                      ? "text-slate-400"
                      : "text-amber-700"
                }
              >
                {statusLabel(inv.status)}
                {inv.status === "open" && inv.overdue_days > 0 && (
                  <> · {t.platOverdueDays.replace("{days}", String(inv.overdue_days))}</>
                )}
              </span>
              {inv.payment_reference && (
                <span className="text-xs text-slate-400">{inv.payment_reference}</span>
              )}
              {inv.status === "open" && (
                <span className="flex gap-2 ml-auto">
                  <Button
                    variant="secondary"
                    disabled={busy}
                    onClick={() => {
                      const ref = window.prompt(t.paymentReference || "Ref.") || "";
                      run(() =>
                        apiPost(`/platform/invoices/${inv.id}/mark-paid`, {
                          payment_reference: ref || null,
                        })
                      );
                    }}
                  >
                    {t.platMarkPaid}
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={busy}
                    onClick={() => run(() => apiPost(`/platform/invoices/${inv.id}/void`, {}))}
                  >
                    {t.platVoid}
                  </Button>
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function TenantCard({
  tenant,
  onAct,
  onUpdate,
}: {
  tenant: TenantRow;
  onAct: (id: string, action: "suspend" | "activate") => void;
  onUpdate: (id: string, patch: Record<string, unknown>) => void;
}) {
  const { t } = useI18n();
  const [editing, setEditing] = useState(false);
  const [seats, setSeats] = useState(String(tenant.seats_limit));
  const [plan, setPlan] = useState(tenant.plan);
  const [extendDays, setExtendDays] = useState("");
  const [price, setPrice] = useState(String(tenant.plan_price_eur));
  const [notes, setNotes] = useState(tenant.billing_notes || "");

  const suspended = tenant.status === "suspended";

  return (
    <Card className="p-5 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <p className="font-semibold">
            {tenant.name}{" "}
            <Badge
              status={suspended ? "missed" : "open"}
              label={suspended ? t.suspended : t.activeLabel}
            />
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {t.planLabel}: {tenant.plan} · {tenant.plan_price_eur.toFixed(2)} {t.platPriceLabel} ·{" "}
            {t.seats}: {tenant.seats_used}/{tenant.seats_limit} ·{" "}
            {t.matters}: {tenant.matters_count}
            {tenant.trial_ends_at &&
              ` · ${t.trialUntil} ${new Date(tenant.trial_ends_at).toLocaleDateString()}`}
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <Button variant="secondary" onClick={() => setEditing(!editing)}>
            {t.edit}
          </Button>
          {suspended ? (
            <Button onClick={() => onAct(tenant.id, "activate")}>{t.activate}</Button>
          ) : (
            <Button variant="secondary" onClick={() => onAct(tenant.id, "suspend")}>
              {t.suspend}
            </Button>
          )}
        </div>
      </div>
      {editing && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-slate-100">
          <div>
            <label className="text-xs text-slate-500">{t.planLabel}</label>
            <select
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="trial">trial</option>
              <option value="solo">solo</option>
              <option value="firm">firm</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500">{t.seats}</label>
            <Input type="number" min={1} value={seats} onChange={(e) => setSeats(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-slate-500">{t.extendTrialDays}</label>
            <Input
              type="number"
              min={1}
              value={extendDays}
              onChange={(e) => setExtendDays(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-slate-500">{t.platPriceLabel}</label>
            <Input
              type="number"
              min={0}
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-slate-500">{t.billingNotes}</label>
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="sm:col-span-2 lg:col-span-4">
            <Button
              onClick={() => {
                const patch: Record<string, unknown> = {
                  plan,
                  seats_limit: Number(seats),
                  plan_price_eur: Number(price),
                  billing_notes: notes,
                };
                if (extendDays) patch.extend_trial_days = Number(extendDays);
                onUpdate(tenant.id, patch);
                setEditing(false);
                setExtendDays("");
              }}
            >
              {t.save}
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
