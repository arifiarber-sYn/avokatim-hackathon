"use client";

import { useCallback, useEffect, useState } from "react";
import { apiDelete, apiDownload, apiGet, apiPost, getToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Expense, Invoice, Matter, TimeEntry } from "@/lib/types";
import { Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner } from "@/components/ui";

const EXPENSE_CATEGORIES = [
  "court_fee", "bailiff", "expert", "travel", "notary", "translation", "other",
] as const;

export default function BillingPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<"time" | "expenses" | "invoices">("time");
  const [matters, setMatters] = useState<Matter[]>([]);

  useEffect(() => {
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.billing}</h1>
      <div className="flex gap-1 border-b border-slate-200 overflow-x-auto whitespace-nowrap">
        {(["time", "expenses", "invoices"] as const).map((key) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`shrink-0 px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === key
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {key === "time" ? t.timeEntries : key === "expenses" ? t.expensesLabel : t.invoices}
          </button>
        ))}
      </div>
      {tab === "time" && <TimeTab matters={matters} />}
      {tab === "expenses" && <ExpensesTab matters={matters} />}
      {tab === "invoices" && <InvoicesTab matters={matters} />}
    </div>
  );
}

function TimeTab({ matters }: { matters: Matter[] }) {
  const { t } = useI18n();
  const [entries, setEntries] = useState<TimeEntry[] | null>(null);
  const [form, setForm] = useState({
    matter_id: "",
    minutes: "60",
    description: "",
    hourly_rate: "",
  });

  const load = useCallback(() => {
    apiGet<TimeEntry[]>("/time-entries").then(setEntries).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    await apiPost("/time-entries", {
      matter_id: form.matter_id,
      started_at: new Date().toISOString(),
      minutes: parseInt(form.minutes),
      description: form.description,
      billable: true,
      hourly_rate: form.hourly_rate || null,
    });
    setForm({ ...form, description: "" });
    load();
  }

  const matterRef = (id: string) => matters.find((m) => m.id === id)?.reference || "";

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <form onSubmit={add} className="flex gap-3 items-end flex-wrap">
          <div className="flex-1 min-w-56">
            <Label>{t.matters}</Label>
            <Select value={form.matter_id} onChange={(e) => setForm({ ...form, matter_id: e.target.value })} required>
              <option value="">—</option>
              {matters.map((m) => (
                <option key={m.id} value={m.id}>{m.reference} — {m.title}</option>
              ))}
            </Select>
          </div>
          <div className="w-24">
            <Label>{t.minutes}</Label>
            <Input type="number" min={1} value={form.minutes} onChange={(e) => setForm({ ...form, minutes: e.target.value })} required />
          </div>
          <div className="w-32">
            <Label>{t.hourlyRate}</Label>
            <Input type="number" step="0.01" value={form.hourly_rate} onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })} />
          </div>
          <div className="flex-[2] min-w-64">
            <Label>{t.description}</Label>
            <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </div>
          <Button type="submit">{t.newTimeEntry}</Button>
        </form>
      </Card>

      {entries === null ? (
        <Spinner />
      ) : (
        <Card>
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[560px]">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                <th className="px-4 py-3">{t.date}</th>
                <th className="px-4 py-3">{t.matters}</th>
                <th className="px-4 py-3">{t.description}</th>
                <th className="px-4 py-3">{t.minutes}</th>
                <th className="px-4 py-3">{t.invoices}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-slate-100">
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(entry.started_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{matterRef(entry.matter_id)}</td>
                  <td className="px-4 py-3">{entry.description}</td>
                  <td className="px-4 py-3">{entry.minutes}</td>
                  <td className="px-4 py-3">{entry.invoice_id ? <Badge status="paid" label="✓" /> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function ExpensesTab({ matters }: { matters: Matter[] }) {
  const { t } = useI18n();
  const [expenses, setExpenses] = useState<Expense[] | null>(null);
  const [form, setForm] = useState({
    matter_id: "",
    incurred_on: new Date().toISOString().slice(0, 10),
    description: "",
    category: "court_fee",
    amount: "",
  });
  const [error, setError] = useState("");

  const catLabel: Record<string, string> = {
    court_fee: t.expCourtFee,
    bailiff: t.expBailiff,
    expert: t.expExpert,
    travel: t.expTravel,
    notary: t.expNotary,
    translation: t.expTranslation,
    other: t.expOther,
  };

  const load = useCallback(() => {
    apiGet<Expense[]>("/expenses").then(setExpenses).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/expenses", {
        matter_id: form.matter_id,
        incurred_on: form.incurred_on,
        description: form.description,
        category: form.category,
        amount: form.amount,
        billable: true,
      });
      setForm({ ...form, description: "", amount: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function remove(id: string) {
    try {
      await apiDelete(`/expenses/${id}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  const matterRef = (id: string) => matters.find((m) => m.id === id)?.reference || "";

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <form onSubmit={add} className="flex gap-3 items-end flex-wrap">
          <div className="flex-1 min-w-56">
            <Label>{t.matters}</Label>
            <Select value={form.matter_id} onChange={(e) => setForm({ ...form, matter_id: e.target.value })} required>
              <option value="">—</option>
              {matters.map((m) => (
                <option key={m.id} value={m.id}>{m.reference} — {m.title}</option>
              ))}
            </Select>
          </div>
          <div>
            <Label>{t.date}</Label>
            <Input type="date" value={form.incurred_on} onChange={(e) => setForm({ ...form, incurred_on: e.target.value })} required />
          </div>
          <div className="w-40">
            <Label>{t.category}</Label>
            <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {EXPENSE_CATEGORIES.map((c) => (
                <option key={c} value={c}>{catLabel[c]}</option>
              ))}
            </Select>
          </div>
          <div className="w-28">
            <Label>{t.amount} (€)</Label>
            <Input type="number" step="0.01" min="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          </div>
          <div className="flex-[2] min-w-56">
            <Label>{t.description}</Label>
            <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </div>
          <Button type="submit">{t.addExpense}</Button>
        </form>
        <div className="mt-2"><ErrorNote message={error} /></div>
      </Card>

      {expenses === null ? (
        <Spinner />
      ) : (
        <Card>
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                <th className="px-4 py-3">{t.date}</th>
                <th className="px-4 py-3">{t.matters}</th>
                <th className="px-4 py-3">{t.category}</th>
                <th className="px-4 py-3">{t.description}</th>
                <th className="px-4 py-3 text-right">{t.amount}</th>
                <th className="px-4 py-3">{t.invoices}</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((exp) => (
                <tr key={exp.id} className="border-b border-slate-100">
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(exp.incurred_on).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{matterRef(exp.matter_id)}</td>
                  <td className="px-4 py-3 text-xs">{catLabel[exp.category] || exp.category}</td>
                  <td className="px-4 py-3">{exp.description}</td>
                  <td className="px-4 py-3 text-right">{Number(exp.amount).toFixed(2)} €</td>
                  <td className="px-4 py-3">{exp.invoice_id ? <Badge status="paid" label="✓" /> : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {!exp.invoice_id && (
                      <button onClick={() => remove(exp.id)} className="text-xs text-red-500 hover:underline">
                        ✕
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </Card>
      )}
    </div>
  );
}

interface ManualItem {
  description: string;
  quantity: string;
  unit_price: string;
}

function InvoicesTab({ matters }: { matters: Matter[] }) {
  const { t } = useI18n();
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [matterId, setMatterId] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<ManualItem[]>([]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<Invoice[]>("/invoices").then(setInvoices).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/invoices", {
        matter_id: matterId || null,
        include_unbilled_time: !!matterId,
        include_unbilled_expenses: !!matterId,
        notes: notes || null,
        items: items
          .filter((i) => i.description.trim() && Number(i.unit_price) > 0)
          .map((i) => ({
            description: i.description,
            quantity: i.quantity || "1",
            unit_price: i.unit_price,
          })),
      });
      setNotes("");
      setItems([]);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  const [payingId, setPayingId] = useState<string | null>(null);
  const [payRef, setPayRef] = useState("");
  const [sendingId, setSendingId] = useState<string | null>(null);

  async function setStatus(id: string, status: string, reference?: string) {
    const params = new URLSearchParams({ new_status: status });
    if (reference) params.set("payment_reference", reference);
    await fetch(`/api/invoices/${id}/status?${params}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    setPayingId(null);
    setPayRef("");
    load();
  }

  async function sendToClient(inv: Invoice) {
    setSendingId(inv.id);
    setNotice("");
    setError("");
    try {
      await apiPost(`/invoices/${inv.id}/send`);
      setNotice(t.invoiceSent);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setSendingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="p-4 space-y-3">
        <form onSubmit={create} className="space-y-3">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-56">
              <Label>{t.matters}</Label>
              <Select value={matterId} onChange={(e) => setMatterId(e.target.value)}>
                <option value="">—</option>
                {matters.map((m) => (
                  <option key={m.id} value={m.id}>{m.reference} — {m.title}</option>
                ))}
              </Select>
            </div>
            <div className="flex-[2] min-w-48">
              <Label>{t.notes}</Label>
              <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
            <Button type="submit">{t.newInvoice}</Button>
          </div>
          {items.map((item, i) => (
            <div key={i} className="flex gap-3 items-end flex-wrap">
              <div className="flex-[2] min-w-56">
                <Label>{t.description}</Label>
                <Input
                  value={item.description}
                  onChange={(e) => {
                    const next = [...items];
                    next[i] = { ...item, description: e.target.value };
                    setItems(next);
                  }}
                />
              </div>
              <div className="w-24">
                <Label>{t.quantity}</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={item.quantity}
                  onChange={(e) => {
                    const next = [...items];
                    next[i] = { ...item, quantity: e.target.value };
                    setItems(next);
                  }}
                />
              </div>
              <div className="w-32">
                <Label>{t.unitPrice} (€)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={item.unit_price}
                  onChange={(e) => {
                    const next = [...items];
                    next[i] = { ...item, unit_price: e.target.value };
                    setItems(next);
                  }}
                />
              </div>
              <button
                type="button"
                onClick={() => setItems(items.filter((_, j) => j !== i))}
                className="text-red-500 text-sm pb-2.5"
              >
                ✕
              </button>
            </div>
          ))}
          <div className="flex gap-4 items-center flex-wrap">
            <button
              type="button"
              onClick={() => setItems([...items, { description: "", quantity: "1", unit_price: "" }])}
              className="text-xs text-indigo-600 hover:underline"
            >
              + {t.addItem}
            </button>
            {matterId && (
              <p className="text-xs text-slate-500">
                ✓ {t.includeUnbilled} · ✓ {t.includeExpenses}
              </p>
            )}
          </div>
        </form>
        <ErrorNote message={error} />
        {notice && <p className="text-sm text-emerald-700">✓ {notice}</p>}
      </Card>

      {invoices === null ? (
        <Spinner />
      ) : (
        <div className="space-y-3">
          {invoices.map((inv) => (
            <Card key={inv.id} className="p-4">
              <div className="flex justify-between items-center flex-wrap gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold">{inv.number}</span>
                    <Badge status={inv.status} label={(t as Record<string, string>)[inv.status]} />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {inv.items.length} × | {t.total}: {inv.currency} {Number(inv.total).toFixed(2)}
                    {inv.vat_rate > 0 && (
                      <>
                        {" "}+ {t.vat} {inv.vat_rate}% ({Number(inv.vat_amount).toFixed(2)}) ={" "}
                        <span className="font-semibold text-slate-700">
                          {inv.currency} {Number(inv.total_with_vat).toFixed(2)}
                        </span>
                      </>
                    )}
                  </p>
                  {inv.status === "paid" && (inv.paid_on || inv.payment_reference) && (
                    <p className="text-xs text-emerald-700 mt-1">
                      ✓ {t.paid}
                      {inv.paid_on && ` · ${new Date(inv.paid_on).toLocaleDateString()}`}
                      {inv.payment_reference && ` · ${t.paymentReference}: ${inv.payment_reference}`}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Button
                    variant="secondary"
                    onClick={() => apiDownload(`/invoices/${inv.id}/pdf`, `fatura-${inv.number}.pdf`)}
                  >
                    {t.downloadPdf}
                  </Button>
                  {inv.status !== "paid" && inv.status !== "void" && (
                    <Button
                      variant="secondary"
                      onClick={() => sendToClient(inv)}
                      disabled={sendingId === inv.id}
                    >
                      {sendingId === inv.id ? t.loading : t.sendToClient}
                    </Button>
                  )}
                  {inv.status === "draft" && (
                    <Button variant="secondary" onClick={() => setStatus(inv.id, "sent")}>{t.markSent}</Button>
                  )}
                  {inv.status === "sent" && payingId !== inv.id && (
                    <Button onClick={() => setPayingId(inv.id)}>{t.markPaid}</Button>
                  )}
                </div>
              </div>
              {payingId === inv.id && (
                <form
                  className="mt-3 pt-3 border-t border-slate-100 flex gap-2 items-end flex-wrap"
                  onSubmit={(e) => {
                    e.preventDefault();
                    setStatus(inv.id, "paid", payRef);
                  }}
                >
                  <div className="flex-1 min-w-56">
                    <Label>{t.paymentReference}</Label>
                    <Input
                      value={payRef}
                      onChange={(e) => setPayRef(e.target.value)}
                      placeholder={t.paymentReferenceHint}
                    />
                  </div>
                  <Button type="submit">{t.markPaid}</Button>
                  <Button type="button" variant="secondary" onClick={() => setPayingId(null)}>
                    {t.cancel}
                  </Button>
                </form>
              )}
              {inv.items.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-1">
                  {inv.items.map((item) => (
                    <div key={item.id} className="flex justify-between text-xs text-slate-600">
                      <span>{item.description}</span>
                      <span>
                        {Number(item.quantity).toFixed(2)} × {Number(item.unit_price).toFixed(2)} ={" "}
                        {Number(item.amount).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
