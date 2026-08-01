"use client";

import { useCallback, useEffect, useState } from "react";
import { apiDelete, apiDownload, apiGet, apiPost, apiPut, getToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import {
  Expense,
  FeeTariffItem,
  Invoice,
  Matter,
  TimeEntry,
  TrustBalance,
  TrustTransaction,
} from "@/lib/types";
import { Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner } from "@/components/ui";

const EXPENSE_CATEGORIES = [
  "court_fee", "bailiff", "expert", "travel", "notary", "translation", "other",
] as const;

export default function BillingPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<"time" | "expenses" | "invoices" | "trust">("time");
  const [matters, setMatters] = useState<Matter[]>([]);

  useEffect(() => {
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => {});
  }, []);

  const tabLabel: Record<typeof tab, string> = {
    time: t.timeEntries,
    expenses: t.expensesLabel,
    invoices: t.invoices,
    trust: t.trustLabel,
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.billing}</h1>
      <PageIntro k="billing" title={t.billingIntroT} body={t.billingIntro} />
      <div className="flex gap-1 border-b border-slate-200 overflow-x-auto whitespace-nowrap">
        {(["time", "expenses", "invoices", "trust"] as const).map((key) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`shrink-0 px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === key
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {tabLabel[key]}
          </button>
        ))}
      </div>
      {tab === "time" && <TimeTab matters={matters} />}
      {tab === "expenses" && <ExpensesTab matters={matters} />}
      {tab === "invoices" && <InvoicesTab matters={matters} />}
      {tab === "trust" && <TrustTab matters={matters} />}
    </div>
  );
}

interface TimeSuggestion {
  id: string;
  matter_id: string;
  matter_reference: string;
  matter_title: string;
  day: string;
  suggested_minutes: number;
  description: string;
}

function TimeTab({ matters }: { matters: Matter[] }) {
  const { t } = useI18n();
  const [entries, setEntries] = useState<TimeEntry[] | null>(null);
  const [suggestions, setSuggestions] = useState<TimeSuggestion[]>([]);
  const [generating, setGenerating] = useState(false);
  const [form, setForm] = useState({
    matter_id: "",
    minutes: "60",
    description: "",
    hourly_rate: "",
  });

  const load = useCallback(() => {
    apiGet<TimeEntry[]>("/time-entries").then(setEntries).catch(() => {});
    apiGet<TimeSuggestion[]>("/time-suggestions").then(setSuggestions).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function generateSuggestions() {
    setGenerating(true);
    try {
      await apiPost("/time-suggestions/generate");
      load();
    } finally {
      setGenerating(false);
    }
  }

  async function acceptSuggestion(id: string) {
    await apiPost(`/time-suggestions/${id}/accept`, {});
    load();
  }

  async function dismissSuggestion(id: string) {
    await apiPost(`/time-suggestions/${id}/dismiss`);
    load();
  }

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

      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h3 className="text-sm font-semibold text-slate-800">{t.tsTitle}</h3>
            <p className="text-xs text-slate-500">{t.tsHint}</p>
          </div>
          <Button variant="secondary" onClick={generateSuggestions} disabled={generating}>
            {generating ? t.loading : t.tsGenerate}
          </Button>
        </div>
        {suggestions.length === 0 ? (
          <p className="text-xs text-slate-400">{t.tsEmpty}</p>
        ) : (
          <ul className="space-y-2">
            {suggestions.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between gap-3 flex-wrap rounded-lg border border-amber-200 bg-amber-50/60 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-sm text-slate-800">
                    <span className="font-mono text-xs text-slate-500 mr-2">
                      {s.matter_reference}
                    </span>
                    {s.description}
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(s.day).toLocaleDateString()} · {s.suggested_minutes} min
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button onClick={() => acceptSuggestion(s.id)}>{t.tsAccept}</Button>
                  <Button variant="secondary" onClick={() => dismissSuggestion(s.id)}>
                    {t.tsDismiss}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
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

interface RvgVvItem {
  code: string;
  vv: string;
  rate: string;
  group: string;
  name: Record<string, string>;
}

interface RvgLine {
  code: string;
  vv: string;
  name: Record<string, string>;
  rate: string | null;
  amount: string;
}

function InvoicesTab({ matters }: { matters: Matter[] }) {
  const { t, locale } = useI18n();
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [matterId, setMatterId] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<ManualItem[]>([]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [tariff, setTariff] = useState<FeeTariffItem[]>([]);

  // Whether an automated card provider (Stripe/Raiffeisen API) is configured;
  // the manual paste-a-link flow is always available.
  const [autoProvider, setAutoProvider] = useState(false);

  const load = useCallback(() => {
    apiGet<Invoice[]>("/invoices").then(setInvoices).catch(() => {});
  }, []);

  // RVG calculator (only German offices — the catalogue endpoint 404s elsewhere)
  const [rvgItems, setRvgItems] = useState<RvgVvItem[]>([]);
  const [rvgOpen, setRvgOpen] = useState(false);
  const [rvgValue, setRvgValue] = useState("");
  const [rvgSelected, setRvgSelected] = useState<string[]>([
    "verfahrensgebuehr", "termingebuehr",
  ]);
  const [rvgRate, setRvgRate] = useState("1.3");
  const [rvgBusy, setRvgBusy] = useState(false);

  useEffect(() => {
    load();
    apiGet<FeeTariffItem[]>("/fee-tariff").then(setTariff).catch(() => {});
    apiGet<{ items: RvgVvItem[] }>("/fee-calc/rvg")
      .then((c) => setRvgItems(c.items))
      .catch(() => {});
    apiGet<{ auto_provider: boolean }>("/payments-config")
      .then((c) => setAutoProvider(c.auto_provider))
      .catch(() => {});
  }, [load]);

  async function addFromRvg() {
    setRvgBusy(true);
    setError("");
    try {
      const result = await apiPost<{ lines: RvgLine[] }>("/fee-calc/rvg", {
        value_eur: Number(rvgValue),
        items: rvgSelected,
        geschaeftsgebuehr_rate: rvgSelected.includes("geschaeftsgebuehr")
          ? Number(rvgRate)
          : undefined,
      });
      setItems((prev) => [
        ...prev,
        ...result.lines.map((line) => ({
          description: `${line.name[locale] || line.name.de} (${line.vv})`,
          quantity: "1",
          unit_price: line.amount,
        })),
      ]);
      setRvgOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setRvgBusy(false);
    }
  }

  function addTariffItem(id: string) {
    const item = tariff.find((x) => x.id === id);
    if (!item) return;
    const name = item.name[locale] || item.name.sq || item.code;
    setItems((prev) => [
      ...prev,
      {
        description: item.tariff_no ? `${name} (${item.tariff_no})` : name,
        quantity: "1",
        unit_price: item.amount,
      },
    ]);
  }

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/invoices", {
        matter_id: matterId || null,
        include_unbilled_time: !!matterId,
        include_unbilled_expenses: !!matterId,
        notes: notes || null,
        // Negative amounts are legitimate (RVG Anrechnung credit lines)
        items: items
          .filter((i) => i.description.trim() && Number(i.unit_price) !== 0)
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

  const [linkingId, setLinkingId] = useState<string | null>(null);
  // Inline editor for pasting a bank pay-by-link URL onto an invoice
  const [manualLinkId, setManualLinkId] = useState<string | null>(null);
  const [manualUrl, setManualUrl] = useState("");

  async function createLink(inv: Invoice) {
    setLinkingId(inv.id);
    setNotice("");
    setError("");
    try {
      await apiPost(`/invoices/${inv.id}/payment-link`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setLinkingId(null);
    }
  }

  async function saveManualLink(invId: string, url: string | null) {
    setError("");
    try {
      await apiPut(`/invoices/${invId}/payment-link`, { url });
      setManualLinkId(null);
      setManualUrl("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
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
            {tariff.length > 0 && (
              <select
                value=""
                onChange={(e) => {
                  if (e.target.value) addTariffItem(e.target.value);
                }}
                className="text-xs text-indigo-600 border border-slate-200 rounded-md px-2 py-1 bg-white max-w-72"
              >
                <option value="">{t.tariffPicker}</option>
                {tariff.map((item) => (
                  <option key={item.id} value={item.id}>
                    {(item.name[locale] || item.name.sq || item.code)} — {Number(item.amount).toFixed(0)} €
                  </option>
                ))}
              </select>
            )}
            {rvgItems.length > 0 && (
              <button
                type="button"
                onClick={() => setRvgOpen((v) => !v)}
                className="text-xs text-indigo-600 hover:underline"
              >
                {t.rvgTitle}
              </button>
            )}
            {matterId && (
              <p className="text-xs text-slate-500">
                ✓ {t.includeUnbilled} · ✓ {t.includeExpenses}
              </p>
            )}
          </div>
          {rvgOpen && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-3">
              <div className="flex gap-3 items-end flex-wrap">
                <div className="w-40">
                  <Label>{t.rvgValue}</Label>
                  <Input
                    type="number"
                    min="1"
                    step="1"
                    value={rvgValue}
                    onChange={(e) => setRvgValue(e.target.value)}
                  />
                </div>
                {rvgSelected.includes("geschaeftsgebuehr") && (
                  <div className="w-32">
                    <Label>{t.rvgGgRate}</Label>
                    <Select value={rvgRate} onChange={(e) => setRvgRate(e.target.value)}>
                      {["0.5", "0.8", "1.0", "1.3", "1.5", "1.8", "2.0", "2.5"].map((r) => (
                        <option key={r} value={r}>{r.replace(".", ",")}</option>
                      ))}
                    </Select>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-1.5">
                {rvgItems.map((item) => (
                  <label key={item.code} className="flex items-center gap-1.5 text-xs text-slate-600">
                    <input
                      type="checkbox"
                      checked={rvgSelected.includes(item.code)}
                      onChange={() =>
                        setRvgSelected((prev) =>
                          prev.includes(item.code)
                            ? prev.filter((c) => c !== item.code)
                            : [...prev, item.code]
                        )
                      }
                      className="rounded border-slate-300"
                    />
                    {(item.name[locale] || item.name.de)} ({item.vv})
                  </label>
                ))}
              </div>
              <Button
                type="button"
                onClick={addFromRvg}
                disabled={rvgBusy || !rvgValue || rvgSelected.length === 0}
              >
                {rvgBusy ? t.loading : t.rvgInsert}
              </Button>
            </div>
          )}
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
                  {rvgItems.length > 0 && (
                    <Button
                      variant="secondary"
                      onClick={() =>
                        apiDownload(
                          `/invoices/${inv.id}/e-invoice.xml`,
                          `${inv.number}-factur-x.xml`
                        )
                      }
                    >
                      {t.eInvoiceXml}
                    </Button>
                  )}
                  {inv.status !== "paid" && inv.status !== "void" && (
                    <Button
                      variant="secondary"
                      onClick={() => sendToClient(inv)}
                      disabled={sendingId === inv.id}
                    >
                      {sendingId === inv.id ? t.loading : t.sendToClient}
                    </Button>
                  )}
                  {autoProvider && inv.status !== "paid" && inv.status !== "void" && !inv.payment_link && (
                    <Button
                      variant="secondary"
                      onClick={() => createLink(inv)}
                      disabled={linkingId === inv.id}
                    >
                      {linkingId === inv.id ? t.loading : t.createPaymentLink}
                    </Button>
                  )}
                  {inv.status !== "paid" && inv.status !== "void" && (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setManualLinkId(manualLinkId === inv.id ? null : inv.id);
                        setManualUrl(inv.payment_link || "");
                      }}
                    >
                      {inv.payment_link ? t.payLinkEditBtn : t.payLinkManualBtn}
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
              {manualLinkId === inv.id && (
                <form
                  className="mt-3 pt-3 border-t border-slate-100 space-y-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    saveManualLink(inv.id, manualUrl.trim() || null);
                  }}
                >
                  <Label>{t.payLinkManualBtn}</Label>
                  <Input
                    type="url"
                    value={manualUrl}
                    onChange={(e) => setManualUrl(e.target.value)}
                    placeholder="https://pay.raiffeisen-kosovo.com/..."
                  />
                  <p className="text-xs text-slate-400">{t.payLinkManualHint}</p>
                  <div className="flex gap-2">
                    <Button type="submit">{t.save}</Button>
                    {inv.payment_link && (
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => saveManualLink(inv.id, null)}
                      >
                        {t.payLinkRemove}
                      </Button>
                    )}
                  </div>
                </form>
              )}
              {inv.payment_link && inv.status !== "paid" && (
                <p className="mt-2 text-xs text-slate-600">
                  {t.paymentLinkLabel}:{" "}
                  <a
                    href={inv.payment_link}
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-600 hover:underline break-all"
                  >
                    {inv.payment_link.slice(0, 60)}…
                  </a>{" "}
                  <button
                    type="button"
                    className="text-indigo-600 hover:underline"
                    onClick={() => navigator.clipboard.writeText(inv.payment_link!)}
                  >
                    ({t.copyLink})
                  </button>
                </p>
              )}
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

function TrustTab({ matters }: { matters: Matter[] }) {
  const { t } = useI18n();
  const [balances, setBalances] = useState<TrustBalance[] | null>(null);
  const [transactions, setTransactions] = useState<TrustTransaction[] | null>(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    matter_id: "",
    kind: "deposit",
    occurred_on: new Date().toISOString().slice(0, 10),
    amount: "",
    description: "",
    reference: "",
    source_of_funds: "",
  });

  const load = useCallback(() => {
    apiGet<TrustBalance[]>("/trust/balances").then(setBalances).catch(() => {});
    apiGet<TrustTransaction[]>("/trust/transactions").then(setTransactions).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/trust/transactions", {
        matter_id: form.matter_id,
        kind: form.kind,
        occurred_on: form.occurred_on,
        amount: form.amount,
        description: form.description,
        reference: form.reference || null,
        source_of_funds: form.source_of_funds || null,
      });
      setForm({ ...form, amount: "", description: "", reference: "", source_of_funds: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function remove(id: string) {
    setError("");
    try {
      await apiDelete(`/trust/transactions/${id}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  const matterRef = (id: string) => matters.find((m) => m.id === id)?.reference || "";

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">{t.trustHint}</p>

      {balances !== null && balances.length > 0 && (
        <Card className="p-4">
          <h2 className="text-sm font-semibold mb-3">{t.trustBalances}</h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {balances.map((b) => (
              <div
                key={b.matter_id}
                className="rounded-lg border border-slate-200 px-3 py-2 flex justify-between items-center"
              >
                <div>
                  <p className="font-mono text-xs text-slate-500">{b.matter_reference}</p>
                  <p className="text-xs text-slate-600 truncate max-w-44">
                    {b.client_name || b.matter_title}
                  </p>
                </div>
                <span
                  className={`font-semibold text-sm ${
                    Number(b.balance) > 0 ? "text-emerald-700" : "text-slate-500"
                  }`}
                >
                  {Number(b.balance).toFixed(2)} €
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

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
          <div className="w-32">
            <Label>{t.trustKind}</Label>
            <Select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
              <option value="deposit">{t.trustDeposit}</option>
              <option value="withdrawal">{t.trustWithdrawal}</option>
            </Select>
          </div>
          <div>
            <Label>{t.date}</Label>
            <Input type="date" value={form.occurred_on} onChange={(e) => setForm({ ...form, occurred_on: e.target.value })} required />
          </div>
          <div className="w-28">
            <Label>{t.amount} (€)</Label>
            <Input type="number" step="0.01" min="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          </div>
          <div className="flex-[2] min-w-48">
            <Label>{t.description}</Label>
            <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </div>
          <div className="w-40">
            <Label>{t.paymentReference}</Label>
            <Input value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} placeholder={t.trustReferenceHint} />
          </div>
          {form.kind === "deposit" && (
            <div className="flex-1 min-w-48">
              <Label>{t.sourceOfFunds}</Label>
              <Input
                value={form.source_of_funds}
                onChange={(e) => setForm({ ...form, source_of_funds: e.target.value })}
              />
            </div>
          )}
          <Button type="submit">{t.addTransaction}</Button>
        </form>
        {/* AML large-amount warning (Law 05/L-096) */}
        {form.kind === "deposit" && Number(form.amount) >= 10000 && (
          <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            ⚠ {t.largeCashWarning}
          </p>
        )}
        <div className="mt-2"><ErrorNote message={error} /></div>
      </Card>

      {transactions === null ? (
        <Spinner />
      ) : (
        <Card>
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                <th className="px-4 py-3">{t.date}</th>
                <th className="px-4 py-3">{t.matters}</th>
                <th className="px-4 py-3">{t.trustKind}</th>
                <th className="px-4 py-3">{t.description}</th>
                <th className="px-4 py-3 text-right">{t.amount}</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.id} className="border-b border-slate-100">
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(txn.occurred_on).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{matterRef(txn.matter_id)}</td>
                  <td className="px-4 py-3">
                    <Badge
                      status={txn.kind === "deposit" ? "paid" : "sent"}
                      label={txn.kind === "deposit" ? t.trustDeposit : t.trustWithdrawal}
                    />
                  </td>
                  <td className="px-4 py-3">
                    {txn.description}
                    {txn.reference && (
                      <span className="text-xs text-slate-400"> · {txn.reference}</span>
                    )}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-medium ${
                      txn.kind === "deposit" ? "text-emerald-700" : "text-slate-700"
                    }`}
                  >
                    {txn.kind === "deposit" ? "+" : "−"}{Number(txn.amount).toFixed(2)} €
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => remove(txn.id)} className="text-xs text-red-500 hover:underline">
                      ✕
                    </button>
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
