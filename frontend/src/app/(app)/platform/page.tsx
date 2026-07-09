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
  billing_notes: string | null;
  created_at: string;
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
    </div>
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
            {t.planLabel}: {tenant.plan} · {t.seats}: {tenant.seats_used}/{tenant.seats_limit} ·{" "}
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
            <label className="text-xs text-slate-500">{t.billingNotes}</label>
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="sm:col-span-2 lg:col-span-4">
            <Button
              onClick={() => {
                const patch: Record<string, unknown> = {
                  plan,
                  seats_limit: Number(seats),
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
