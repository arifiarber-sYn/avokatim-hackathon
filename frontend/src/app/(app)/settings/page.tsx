"use client";

import { useCallback, useEffect, useState } from "react";
import { apiDownload, apiGet, apiPatch, apiPost, apiPut, apiUpload, setToken } from "@/lib/api";
import { clientCountry, DE_REGIONS } from "@/lib/country";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import { Contact } from "@/lib/types";
import { Button, Card, ErrorNote, Input, Label, Select, Textarea } from "@/components/ui";

interface Me {
  email: string;
  totp_enabled: boolean;
}

interface CorpusDoc {
  id: string;
  title: string;
  reference: string | null;
  chunk_count: number;
}

// 18 cards need a map: settings are grouped in 5 anchored sections with a
// sticky sidebar on desktop and a horizontal chip bar on mobile.
const GROUP_IDS = ["zyra", "publik", "ai", "njoftimet", "siguria"] as const;

export default function SettingsPage() {
  const { t } = useI18n();
  const [isAdmin, setIsAdmin] = useState(false);
  const [isNotary, setIsNotary] = useState(false);

  useEffect(() => {
    apiGet<{ role: string; tenant_profession?: string }>("/auth/me")
      .then((me) => {
        setIsAdmin(me.role === "admin");
        setIsNotary(me.tenant_profession === "notary");
      })
      .catch(() => {});
  }, []);

  const groupLabels: Record<(typeof GROUP_IDS)[number], string> = {
    zyra: t.setGrpOffice,
    publik: t.setGrpPublic,
    ai: t.setGrpAI,
    njoftimet: t.setGrpNotifs,
    siguria: t.setGrpSecurity,
  };

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold">{t.settings}</h1>

      {/* Mobile: horizontal chip bar (sticky) */}
      <nav className="lg:hidden sticky top-0 z-20 -mx-4 px-4 py-2.5 mt-4 bg-slate-50/95 backdrop-blur border-b border-slate-100 flex gap-2 overflow-x-auto">
        {GROUP_IDS.map((id) => (
          <a
            key={id}
            href={`#grp-${id}`}
            className="shrink-0 text-xs font-medium bg-white border border-slate-200 text-slate-600 rounded-full px-3 py-1.5 hover:border-indigo-300 hover:text-indigo-700"
          >
            {groupLabels[id]}
          </a>
        ))}
      </nav>

      <div className="flex gap-8 mt-6">
        {/* Desktop: sticky sidebar */}
        <aside className="hidden lg:block w-48 shrink-0">
          <nav className="sticky top-6 space-y-1">
            {GROUP_IDS.map((id) => (
              <a
                key={id}
                href={`#grp-${id}`}
                className="block text-sm text-slate-500 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg px-3 py-2 transition"
              >
                {groupLabels[id]}
              </a>
            ))}
          </nav>
        </aside>

        <div className="flex-1 min-w-0 max-w-3xl space-y-10">
          <PageIntro k="settings" title={t.settingsIntroT} body={t.settingsIntro} />

          <SettingsGroup id="zyra" title={groupLabels.zyra}>
            <ProfileSection />
            <FirmSection />
            <TeamSection />
            <ImportSection />
          </SettingsGroup>

          <SettingsGroup id="publik" title={groupLabels.publik}>
            <PublicProfileSection isNotary={isNotary} />
            <BookingSection />
            {!isNotary && <ReferralSection />}
            <PublicIntakeSection />
          </SettingsGroup>

          <SettingsGroup id="ai" title={groupLabels.ai}>
            <AvaStyleSection />
            <CorpusSection />
          </SettingsGroup>

          <SettingsGroup id="njoftimet" title={groupLabels.njoftimet}>
            <PushSection />
            <CalendarFeedSection />
          </SettingsGroup>

          <SettingsGroup id="siguria" title={groupLabels.siguria}>
            <TwoFASection />
            <PortalSection />
            {isAdmin && <SubscriptionSection />}
            {isAdmin && <ComplianceSection />}
            {isAdmin && <AuditLogSection />}
            {isAdmin && <ExportSection />}
          </SettingsGroup>
        </div>
      </div>
    </div>
  );
}

function SettingsGroup({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={`grp-${id}`} className="scroll-mt-16 space-y-5">
      <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-slate-200 pb-2">
        {title}
      </h2>
      <div className="space-y-6">{children}</div>
    </section>
  );
}

/** Platform subscription: plan, price, invoices, upgrade from trial.
    Citizens never pay; the lawyer pays per seat — never a fee share. */
function SubscriptionSection() {
  const { t } = useI18n();
  const [sub, setSub] = useState<{
    plan: string;
    trial_ends_at: string | null;
    price_eur: number;
    seats: number;
    monthly_total_eur: number;
    free_forever: boolean;
    past_due: boolean;
    card_payments: boolean;
    bank_details: string | null;
    invoices: {
      id: string;
      number: string;
      period_start: string;
      seats: number;
      amount_eur: number;
      status: string;
      due_on: string;
      paid_on: string | null;
      payment_link: string | null;
    }[];
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [upgraded, setUpgraded] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<NonNullable<typeof sub>>("/billing/subscription").then(setSub).catch(() => {});
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  if (sub === null) return null;

  const statusLabel = (s: string) =>
    s === "paid" ? t.subStatusPaid : s === "void" ? t.subStatusVoid : t.subStatusOpen;

  async function upgrade() {
    setBusy(true);
    setError("");
    try {
      await apiPost("/billing/subscription/upgrade", {});
      setUpgraded(true);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    } finally {
      setBusy(false);
    }
  }

  async function payCard(invoiceId: string) {
    setBusy(true);
    setError("");
    try {
      const inv = await apiPost<{ payment_link: string | null }>(
        `/billing/subscription/invoices/${invoiceId}/payment-link`,
        {}
      );
      if (inv.payment_link) window.open(inv.payment_link, "_blank");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-6 space-y-4">
      <h2 className="text-lg font-semibold">{t.subTitle}</h2>
      <ErrorNote message={error} />
      {sub.past_due && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-2">
          {t.subPastDue}
        </div>
      )}
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <span>
          {t.planLabel}: <b>{sub.plan}</b>
          {sub.free_forever && <> — {t.subFreeForever}</>}
        </span>
        <span>
          {sub.price_eur.toFixed(2)} {t.subPricePerUser} × {sub.seats}
        </span>
        <span>
          {t.subTotalMonthly}: <b>{sub.monthly_total_eur.toFixed(2)} €</b>
        </span>
      </div>
      {sub.plan === "trial" && (
        <div className="space-y-2">
          {sub.trial_ends_at && (
            <p className="text-sm text-slate-600">
              {t.subTrialUntil.replace(
                "{date}",
                new Date(sub.trial_ends_at).toLocaleDateString()
              )}
            </p>
          )}
          <p className="text-xs text-slate-500">
            {t.subUpgradeHint.replace("{price}", sub.price_eur.toFixed(2))}
          </p>
          {upgraded ? (
            <p className="text-sm text-emerald-700">{t.subUpgraded}</p>
          ) : (
            <Button onClick={upgrade} disabled={busy}>
              {t.subUpgrade}
            </Button>
          )}
        </div>
      )}
      <div>
        <h3 className="text-sm font-semibold mb-2">{t.subInvoicesTitle}</h3>
        {sub.invoices.length === 0 ? (
          <p className="text-sm text-slate-500">{t.subNoInvoices}</p>
        ) : (
          <div className="space-y-2">
            {sub.invoices.map((inv) => (
              <div
                key={inv.id}
                className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm border border-slate-200 rounded-lg px-3 py-2"
              >
                <span className="font-mono">{inv.number}</span>
                <span className="text-slate-500">
                  {t.subPeriod}: {new Date(inv.period_start).toLocaleDateString(undefined, { month: "2-digit", year: "numeric" })}
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
                </span>
                {inv.status === "open" && sub.card_payments && (
                  <Button variant="secondary" onClick={() => payCard(inv.id)} disabled={busy}>
                    {t.subPayCard}
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
        {sub.bank_details && sub.invoices.some((i) => i.status === "open") && (
          <p className="text-xs text-slate-500 mt-2 whitespace-pre-line">
            {t.subBankHint} {sub.bank_details}
          </p>
        )}
      </div>
    </Card>
  );
}

/** Data protection (Law 06/L-082) + AML (Law 05/L-096) firm settings:
    retention period, external-AI gate, compliance officer, retention review. */
function ComplianceSection() {
  const { t } = useI18n();
  const [retention, setRetention] = useState("10");
  const [allowAi, setAllowAi] = useState(true);
  const [officerId, setOfficerId] = useState("");
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [review, setReview] = useState<{
    matters: { id: string; reference: string; title: string; closed_on: string }[];
  } | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<{ retention_years: number; allow_external_ai: boolean; compliance_officer_id: string | null }>("/firm")
      .then((r) => {
        setRetention(String(r.retention_years ?? 10));
        setAllowAi(r.allow_external_ai ?? true);
        setOfficerId(r.compliance_officer_id || "");
      })
      .catch(() => {});
    apiGet<TeamMember[]>("/team").then(setMembers).catch(() => {});
    apiGet<{ matters: { id: string; reference: string; title: string; closed_on: string }[] }>(
      "/privacy/retention-review"
    )
      .then(setReview)
      .catch(() => {});
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      await apiPatch("/firm", {
        retention_years: Number(retention),
        allow_external_ai: allowAi,
        compliance_officer_id: officerId || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-5 space-y-4">
      <h2 className="font-semibold">{t.privacyTitle}</h2>
      <form onSubmit={save} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <Label>{t.retentionYears}</Label>
            <Input
              type="number"
              min={1}
              max={100}
              value={retention}
              onChange={(e) => setRetention(e.target.value)}
            />
            <p className="text-xs text-slate-400 mt-1">{t.retentionHint}</p>
          </div>
          <div>
            <Label>{t.complianceOfficer}</Label>
            <Select value={officerId} onChange={(e) => setOfficerId(e.target.value)}>
              <option value="">—</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>{m.full_name}</option>
              ))}
            </Select>
          </div>
        </div>
        <label className="flex items-start gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={allowAi}
            onChange={(e) => setAllowAi(e.target.checked)}
            className="mt-0.5 accent-indigo-600"
          />
          <span>
            {t.allowExternalAi}
            <span className="block text-xs text-slate-400">{t.allowExternalAiHint}</span>
          </span>
        </label>
        <div className="flex items-center gap-3">
          <Button type="submit">{t.save}</Button>
          {saved && <span className="text-sm text-emerald-700">✓ {t.saved}</span>}
          <ErrorNote message={error} />
        </div>
      </form>
      <div className="pt-3 border-t border-slate-100 space-y-2">
        <p className="text-sm font-medium">{t.retentionReview}</p>
        {!review || review.matters.length === 0 ? (
          <p className="text-xs text-slate-400">{t.retentionEmpty}</p>
        ) : (
          review.matters.map((m) => (
            <p key={m.id} className="text-sm text-slate-600">
              • <span className="font-mono text-xs">{m.reference}</span> {m.title}{" "}
              <span className="text-xs text-slate-400">
                — {t.closedOn} {new Date(m.closed_on).toLocaleDateString()}
              </span>
            </p>
          ))
        )}
      </div>
    </Card>
  );
}

interface AuditEntry {
  id: string;
  at: string;
  user: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: Record<string, unknown>;
}

function AuditLogSection() {
  const { t } = useI18n();
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [filter, setFilter] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const q = filter ? `?action=${encodeURIComponent(filter)}` : "";
    apiGet<AuditEntry[]>(`/audit-log${q}`).then(setEntries).catch(() => {});
  }, [open, filter]);

  return (
    <Card className="p-5 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">{t.auditLogLabel}</h2>
          <p className="text-xs text-slate-500 mt-0.5">{t.auditLogHint}</p>
        </div>
        <Button variant="secondary" onClick={() => setOpen(!open)}>
          {open ? t.close : t.show}
        </Button>
      </div>
      {open && (
        <>
          <div className="w-64">
            <Label>{t.actionLabel}</Label>
            <Input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="p.sh. matter, invoice, document"
            />
          </div>
          <div className="overflow-x-auto max-h-96 overflow-y-auto border border-slate-100 rounded-lg">
            <table className="w-full text-xs min-w-[560px]">
              <thead className="sticky top-0 bg-slate-50">
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="px-3 py-2">{t.date}</th>
                  <th className="px-3 py-2">{t.name}</th>
                  <th className="px-3 py-2">{t.actionLabel}</th>
                  <th className="px-3 py-2">{t.description}</th>
                </tr>
              </thead>
              <tbody>
                {(entries || []).map((e) => (
                  <tr key={e.id} className="border-b border-slate-50">
                    <td className="px-3 py-1.5 text-slate-500 whitespace-nowrap">
                      {new Date(e.at).toLocaleString()}
                    </td>
                    <td className="px-3 py-1.5">{e.user || "—"}</td>
                    <td className="px-3 py-1.5 font-mono">{e.action}</td>
                    <td className="px-3 py-1.5 text-slate-500 max-w-64 truncate">
                      {Object.entries(e.details || {})
                        .map(([k, v]) => `${k}: ${String(v)}`)
                        .join(" · ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Card>
  );
}

function ExportSection() {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);

  async function download() {
    setBusy(true);
    try {
      await apiDownload(
        "/export/tenant",
        `avokatim-eksporti-${new Date().toISOString().slice(0, 10)}.zip`
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 space-y-3">
      <h2 className="font-semibold">{t.dataExport}</h2>
      <p className="text-sm text-slate-500">{t.dataExportHint}</p>
      <Button onClick={download} disabled={busy}>
        {busy ? t.loading : t.exportDownload}
      </Button>
    </Card>
  );
}

function FirmSection() {
  const { t } = useI18n();
  const [form, setForm] = useState({
    name: "",
    fiscal_number: "",
    vat_number: "",
    address: "",
    bank_details: "",
    iban: "",
    default_vat_rate: "18",
    region: "",
    datev_consultant_no: "",
    datev_client_no: "",
    datev_revenue_account: "",
    datev_debtor_account: "",
  });
  const [logo, setLogo] = useState<string | null>(null);
  const [require2fa, setRequire2fa] = useState(false);
  const [saved, setSaved] = useState(false);
  const [firmIsDE, setFirmIsDE] = useState(false);
  useEffect(() => setFirmIsDE(clientCountry() === "DE"), []);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<{
      name: string;
      fiscal_number: string | null;
      vat_number: string | null;
      address: string | null;
      bank_details: string | null;
      iban: string | null;
      default_vat_rate: number;
      region: string | null;
      logo: string | null;
      require_2fa: boolean;
      datev_consultant_no: string | null;
      datev_client_no: string | null;
      datev_revenue_account: string | null;
      datev_debtor_account: string | null;
    }>("/firm")
      .then((r) => {
        setForm({
          name: r.name || "",
          fiscal_number: r.fiscal_number || "",
          vat_number: r.vat_number || "",
          address: r.address || "",
          bank_details: r.bank_details || "",
          iban: r.iban || "",
          default_vat_rate: String(r.default_vat_rate ?? 18),
          region: r.region || "",
          datev_consultant_no: r.datev_consultant_no || "",
          datev_client_no: r.datev_client_no || "",
          datev_revenue_account: r.datev_revenue_account || "",
          datev_debtor_account: r.datev_debtor_account || "",
        });
        setLogo(r.logo || null);
        setRequire2fa(r.require_2fa || false);
      })
      .catch(() => {});
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      await apiPatch("/firm", {
        name: form.name || undefined,
        fiscal_number: form.fiscal_number || null,
        vat_number: form.vat_number || null,
        address: form.address || null,
        bank_details: form.bank_details || null,
        iban: form.iban || null,
        default_vat_rate: Number(form.default_vat_rate),
        region: form.region || null,
        datev_consultant_no: form.datev_consultant_no || null,
        datev_client_no: form.datev_client_no || null,
        datev_revenue_account: form.datev_revenue_account || null,
        datev_debtor_account: form.datev_debtor_account || null,
        logo,
        require_2fa: require2fa,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  function onLogoFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 200 * 1024) {
      setError(t.logoTooLarge);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setLogo(reader.result as string);
    reader.readAsDataURL(file);
  }

  return (
    <Card className="p-5 space-y-4">
      <div>
        <h2 className="font-semibold">{t.firmProfile}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.firmProfileHint}</p>
      </div>
      <form onSubmit={save} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2">
          <Label>{t.firmName}</Label>
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <Label>{t.fiscalNumber}</Label>
          <Input
            value={form.fiscal_number}
            onChange={(e) => setForm({ ...form, fiscal_number: e.target.value })}
            placeholder="NUI"
          />
        </div>
        <div>
          <Label>{t.vatNumber}</Label>
          <Input
            value={form.vat_number}
            onChange={(e) => setForm({ ...form, vat_number: e.target.value })}
          />
        </div>
        <div className="sm:col-span-2">
          <Label>{t.address}</Label>
          <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
        </div>
        <div className="sm:col-span-2">
          <Label>{t.bankDetails}</Label>
          <Input
            value={form.bank_details}
            onChange={(e) => setForm({ ...form, bank_details: e.target.value })}
            placeholder="Banka Ekonomike · XK05 1234 5678 9012 3456"
          />
          <p className="text-xs text-slate-400 mt-1">{t.bankDetailsHint}</p>
        </div>
        {firmIsDE && (
          <div className="sm:col-span-2">
            <Label>{t.firmIban}</Label>
            <Input
              value={form.iban}
              onChange={(e) => setForm({ ...form, iban: e.target.value })}
              placeholder="DE89 3704 0044 0532 0130 00"
              maxLength={34}
            />
            <p className="text-xs text-slate-400 mt-1">{t.firmIbanHint}</p>
          </div>
        )}
        <div>
          <Label>{t.defaultVatRate}</Label>
          <Input
            type="number"
            min={0}
            max={30}
            value={form.default_vat_rate}
            onChange={(e) => setForm({ ...form, default_vat_rate: e.target.value })}
          />
        </div>
        {firmIsDE && (
          <div>
            <Label>{t.firmRegion}</Label>
            <Select
              value={form.region}
              onChange={(e) => setForm({ ...form, region: e.target.value })}
            >
              <option value="">—</option>
              {DE_REGIONS.map((r) => (
                <option key={r.code} value={r.code}>{r.name}</option>
              ))}
            </Select>
            <p className="text-xs text-slate-400 mt-1">{t.firmRegionHint}</p>
          </div>
        )}
        {firmIsDE && (
          <div className="sm:col-span-2 rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-2">
            <p className="text-sm font-medium text-slate-700">{t.datevTitle}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <Label>{t.datevConsultant}</Label>
                <Input
                  value={form.datev_consultant_no}
                  onChange={(e) => setForm({ ...form, datev_consultant_no: e.target.value })}
                  maxLength={7}
                />
              </div>
              <div>
                <Label>{t.datevClient}</Label>
                <Input
                  value={form.datev_client_no}
                  onChange={(e) => setForm({ ...form, datev_client_no: e.target.value })}
                  maxLength={5}
                />
              </div>
              <div>
                <Label>{t.datevRevenue}</Label>
                <Input
                  value={form.datev_revenue_account}
                  onChange={(e) => setForm({ ...form, datev_revenue_account: e.target.value })}
                  placeholder="8400"
                  maxLength={9}
                />
              </div>
              <div>
                <Label>{t.datevDebtor}</Label>
                <Input
                  value={form.datev_debtor_account}
                  onChange={(e) => setForm({ ...form, datev_debtor_account: e.target.value })}
                  placeholder="10000"
                  maxLength={9}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400">{t.datevHint}</p>
          </div>
        )}
        <div className="sm:col-span-2 space-y-1">
          <Label>{t.firmLogo}</Label>
          <div className="flex items-center gap-3">
            {logo && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={logo} alt="logo" className="h-10 w-10 rounded object-contain border border-slate-200 bg-white" />
            )}
            <input type="file" accept="image/*" onChange={onLogoFile} className="text-xs" />
            {logo && (
              <button type="button" onClick={() => setLogo(null)} className="text-xs text-red-600 hover:underline">
                {t.remove}
              </button>
            )}
          </div>
          <p className="text-xs text-slate-400">{t.firmLogoHint}</p>
        </div>
        <div className="sm:col-span-2 flex items-center gap-2">
          <input
            id="require2fa"
            type="checkbox"
            checked={require2fa}
            onChange={(e) => setRequire2fa(e.target.checked)}
            className="h-4 w-4"
          />
          <label htmlFor="require2fa" className="text-sm">
            {t.require2faPolicy}
          </label>
        </div>
        <div className="sm:col-span-2 flex items-center gap-3">
          <Button type="submit">{t.save}</Button>
          {saved && <span className="text-sm text-emerald-700">✓ {t.saved}</span>}
          <ErrorNote message={error} />
        </div>
      </form>
    </Card>
  );
}

function ImportSection() {
  const { t } = useI18n();
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function importFile(kind: "contacts" | "matters", e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setResult("");
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await apiUpload<{ created: number; skipped?: number; errors: string[] }>(
        `/import/${kind}`,
        form
      );
      let msg = `${t.importedCount}: ${r.created}`;
      if (r.skipped) msg += ` · ${t.skippedCount}: ${r.skipped}`;
      if (r.errors?.length) msg += ` · ${t.errorsCount}: ${r.errors.length} (${r.errors[0]})`;
      setResult(msg);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  function templateCsv(kind: "contacts" | "matters") {
    const content =
      kind === "contacts"
        ? "display_name,kind,email,phone,address,national_id,notes\nFilan Fisteku,person,filan@shembull.com,+38344123456,Prishtinë,,\n"
        : "title,practice_area,status,client_name,court_name,court_case_number,opened_on,description\nKontest pronësor,civil,open,Filan Fisteku,Gjykata Themelore Prishtinë,C-123/2026,2026-01-15,\n";
    const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = kind === "contacts" ? "shabllon-kontaktet.csv" : "shabllon-lendet.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Card className="p-5 space-y-4">
      <div>
        <h2 className="font-semibold">{t.dataImport}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.dataImportHint}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(["contacts", "matters"] as const).map((kind) => (
          <div key={kind} className="border border-slate-200 rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium">
              {kind === "contacts" ? t.importContacts : t.importMatters}
            </p>
            <label className="cursor-pointer inline-block">
              <span className="px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-700 inline-block">
                {busy ? t.loading : t.chooseCsv}
              </span>
              <input
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                disabled={busy}
                onChange={(e) => importFile(kind, e)}
              />
            </label>
            <button
              type="button"
              onClick={() => templateCsv(kind)}
              className="block text-xs text-indigo-600 hover:underline"
            >
              {t.downloadTemplate}
            </button>
          </div>
        ))}
      </div>
      {result && <p className="text-sm text-emerald-700">✓ {result}</p>}
      <ErrorNote message={error} />
    </Card>
  );
}

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}

function PushSection() {
  const { t } = useI18n();
  const [supported, setSupported] = useState(true);
  const [serverEnabled, setServerEnabled] = useState(false);
  const [vapidKey, setVapidKey] = useState("");
  const [subscribed, setSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setSupported(false);
      return;
    }
    apiGet<{ key: string; enabled: boolean }>("/push/vapid-public-key")
      .then((r) => {
        setServerEnabled(r.enabled);
        setVapidKey(r.key);
      })
      .catch(() => {});
    navigator.serviceWorker.register("/sw.js").then(async (reg) => {
      const sub = await reg.pushManager.getSubscription();
      setSubscribed(!!sub);
    });
  }, []);

  async function enable() {
    setBusy(true);
    setError("");
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") throw new Error(t.error);
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey) as BufferSource,
      });
      const json = sub.toJSON();
      await apiPost("/push/subscribe", {
        endpoint: sub.endpoint,
        p256dh: json.keys?.p256dh,
        auth: json.keys?.auth,
        user_agent: navigator.userAgent,
      });
      setSubscribed(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setBusy(true);
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await apiPost("/push/unsubscribe", { endpoint: sub.endpoint });
        await sub.unsubscribe();
      }
      setSubscribed(false);
    } finally {
      setBusy(false);
    }
  }

  // iOS supports web push only from an installed PWA (iOS 16.4+): show the
  // "Add to Home Screen" guide instead of a dead "not supported" message.
  const isIos =
    typeof navigator !== "undefined" && /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isStandalone =
    typeof window !== "undefined" &&
    window.matchMedia?.("(display-mode: standalone)").matches;

  return (
    <Card className="p-5 space-y-3">
      <h2 className="font-semibold">{t.pushNotifications}</h2>
      <p className="text-sm text-slate-500">{t.pushHint}</p>
      {isIos && !isStandalone && !supported ? (
        <div className="text-sm bg-sky-50 text-sky-800 rounded-lg p-3 space-y-1">
          <p className="font-semibold">{t.pushIosT}</p>
          <p>{t.pushIosGuide}</p>
        </div>
      ) : !supported || !serverEnabled ? (
        <p className="text-sm text-slate-400">{t.pushNotSupported}</p>
      ) : subscribed ? (
        <div className="flex items-center gap-3">
          <span className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
            ✓ {t.pushEnabled}
          </span>
          <Button variant="secondary" onClick={disable} disabled={busy}>
            {t.disablePushDevice}
          </Button>
        </div>
      ) : (
        <Button onClick={enable} disabled={busy}>
          {busy ? t.loading : t.enablePushDevice}
        </Button>
      )}
      <ErrorNote message={error} />
    </Card>
  );
}

interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  invite_pending?: boolean;
}

function TeamSection() {
  const { t } = useI18n();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [form, setForm] = useState({ full_name: "", email: "", role: "lawyer" });
  const [error, setError] = useState("");
  const [invited, setInvited] = useState(false);

  const roleLabels: Record<string, string> = {
    admin: t.roleAdmin,
    lawyer: t.roleLawyer,
    staff: t.roleStaff,
  };

  const load = useCallback(() => {
    apiGet<TeamMember[]>("/team").then(setMembers).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setInvited(false);
    try {
      await apiPost("/team/invite", form);
      setForm({ full_name: "", email: "", role: "lawyer" });
      setInvited(true);
      setTimeout(() => setInvited(false), 4000);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function resendInvite(m: TeamMember) {
    try {
      await apiPost(`/team/${m.id}/resend-invite`, {});
      setInvited(true);
      setTimeout(() => setInvited(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function toggleActive(m: TeamMember) {
    try {
      await apiPatch(`/team/${m.id}`, { is_active: !m.is_active });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function changeRole(m: TeamMember, role: string) {
    try {
      await apiPatch(`/team/${m.id}`, { role });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-5 space-y-4">
      <h2 className="font-semibold">{t.team}</h2>
      <div className="divide-y divide-slate-100">
        {members.map((m) => (
          <div key={m.id} className="flex items-center justify-between py-2 text-sm gap-3">
            <div className="min-w-0">
              <p className={`font-medium truncate ${m.is_active ? "" : "text-slate-400 line-through"}`}>
                {m.full_name}
                {m.invite_pending && (
                  <span className="ml-2 text-[10px] uppercase tracking-wide text-amber-600 bg-amber-50 rounded px-1.5 py-0.5 no-underline inline-block">
                    {t.invitePending}
                  </span>
                )}
              </p>
              <p className="text-xs text-slate-500 truncate">{m.email}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Select
                value={m.role}
                onChange={(e) => changeRole(m, e.target.value)}
                className="text-xs w-36"
              >
                {Object.entries(roleLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </Select>
              {m.invite_pending ? (
                <button
                  onClick={() => resendInvite(m)}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  {t.resendInvite}
                </button>
              ) : (
                <button
                  onClick={() => toggleActive(m)}
                  className={`text-xs hover:underline ${m.is_active ? "text-red-600" : "text-emerald-600"}`}
                >
                  {m.is_active ? t.deactivate : t.activate}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={add} className="grid md:grid-cols-2 gap-3 pt-2 border-t border-slate-100">
        <div>
          <Label>{t.fullName}</Label>
          <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        </div>
        <div>
          <Label>{t.email}</Label>
          <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </div>
        <div>
          <Label>{t.roleLabel}</Label>
          <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {Object.entries(roleLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
        </div>
        <div className="md:col-span-2 flex items-center gap-3">
          <Button type="submit">{t.sendInvite}</Button>
          {invited && <span className="text-sm text-emerald-700">✓ {t.inviteSent}</span>}
          <ErrorNote message={error} />
        </div>
      </form>
    </Card>
  );
}

function CopyLinkCard({ title, hint, url }: { title: string; hint: string; url: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Card className="p-5 space-y-3">
      <h2 className="font-semibold">{title}</h2>
      <p className="text-sm text-slate-500">{hint}</p>
      {url && (
        <div className="flex gap-2 items-center">
          <p className="flex-1 font-mono text-xs bg-slate-100 rounded-lg px-3 py-2 break-all select-all">
            {url}
          </p>
          <Button variant="secondary" onClick={copy}>
            {copied ? t.copied : t.copyLink}
          </Button>
        </div>
      )}
    </Card>
  );
}

function CalendarFeedSection() {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  useEffect(() => {
    apiGet<{ url: string }>("/calendar/feed-url").then((r) => setUrl(r.url)).catch(() => {});
  }, []);
  return <CopyLinkCard title={t.calendarSync} hint={t.calendarSyncHint} url={url} />;
}

function PublicIntakeSection() {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  useEffect(() => {
    apiGet<{ url: string }>("/intake/public-form").then((r) => setUrl(r.url)).catch(() => {});
  }, []);
  return <CopyLinkCard title={t.publicIntakeForm} hint={t.publicIntakeHint} url={url} />;
}

function ProfileSection() {
  const { t } = useI18n();
  const [target, setTarget] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiGet<{ billable_hours_target_monthly: number }>("/auth/me")
      .then((me) => setTarget(String(me.billable_hours_target_monthly)))
      .catch(() => {});
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    try {
      await apiPatch("/auth/me", { billable_hours_target_monthly: Number(target) });
      setMessage("✓");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-5 space-y-4">
      <h2 className="font-semibold">{t.profile}</h2>
      <form onSubmit={save} className="flex gap-3 items-end flex-wrap">
        <div className="w-64">
          <Label>{t.monthlyHoursTarget}</Label>
          <Input
            type="number"
            min={1}
            max={744}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            required
          />
        </div>
        <Button type="submit">{t.save}</Button>
        {message && <span className="text-sm">{message}</span>}
      </form>
      <ChangePasswordForm />
    </Card>
  );
}

function ChangePasswordForm() {
  const { t } = useI18n();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function change(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const res = await apiPost<{ changed: boolean; access_token?: string }>(
        "/auth/change-password",
        { current_password: current, new_password: next },
      );
      // the backend revokes all sessions on password change and hands this
      // device a fresh token — store it so the user stays logged in here
      if (res.access_token) setToken(res.access_token);
      setCurrent("");
      setNext("");
      setMessage("✓ " + t.passwordChanged);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <form onSubmit={change} className="pt-3 border-t border-slate-100 space-y-3">
      <p className="text-sm font-medium">{t.changePassword}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <Label>{t.currentPassword}</Label>
          <Input
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
          />
        </div>
        <div>
          <Label>{t.newPassword}</Label>
          <Input
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            required
            minLength={10}
          />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Button type="submit" variant="secondary">{t.changePassword}</Button>
        {message && <span className="text-sm text-emerald-700">{message}</span>}
        <ErrorNote message={error} />
      </div>
    </form>
  );
}

function TwoFASection() {
  const { t } = useI18n();
  const [me, setMe] = useState<Me | null>(null);
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<Me>("/auth/me").then(setMe).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function start() {
    setSetup(await apiPost("/auth/2fa/setup"));
  }

  async function enable(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/auth/2fa/enable", { code });
      setSetup(null);
      setCode("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-5 space-y-4">
      <h2 className="font-semibold">{t.security}</h2>
      {me?.totp_enabled ? (
        <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2 inline-block">
          ✓ {t.twoFAEnabled}
        </p>
      ) : setup ? (
        <form onSubmit={enable} className="space-y-3">
          <p className="text-sm text-slate-600">{t.scan2FA}</p>
          <p className="font-mono text-sm bg-slate-100 rounded-lg p-3 break-all select-all">
            {setup.secret}
          </p>
          <p className="font-mono text-xs bg-slate-50 rounded-lg p-2 break-all text-slate-500">
            {setup.otpauth_uri}
          </p>
          <div className="flex gap-2 items-end">
            <div>
              <Label>{t.confirm2FACode}</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} maxLength={8} required />
            </div>
            <Button type="submit">{t.verify}</Button>
          </div>
          <ErrorNote message={error} />
        </form>
      ) : (
        <Button onClick={start}>{t.enable2FA}</Button>
      )}
    </Card>
  );
}

function CorpusSection() {
  const { t } = useI18n();
  const [docs, setDocs] = useState<CorpusDoc[]>([]);
  const [form, setForm] = useState({ title: "", reference: "", text: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<CorpusDoc[]>("/corpus?jurisdiction_code=XK").then(setDocs).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiPost("/corpus", {
        jurisdiction_code: "XK",
        title: form.title,
        reference: form.reference || null,
        text: form.text,
        language: "sq",
      });
      setForm({ title: "", reference: "", text: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 space-y-4">
      <h2 className="font-semibold">{t.legalCorpus}</h2>
      {docs.length > 0 && (
        <div className="space-y-1">
          {docs.map((d) => (
            <p key={d.id} className="text-sm text-slate-600">
              • {d.title} {d.reference && <span className="text-slate-400">({d.reference})</span>}{" "}
              <span className="text-xs text-slate-400">— {d.chunk_count} {t.chunks}</span>
            </p>
          ))}
        </div>
      )}
      <form onSubmit={add} className="space-y-3">
        <div className="grid md:grid-cols-2 gap-3">
          <div>
            <Label>{t.lawTitle}</Label>
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </div>
          <div>
            <Label>{t.lawReference}</Label>
            <Input value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
          </div>
        </div>
        <div>
          <Label>{t.lawText}</Label>
          <Textarea rows={6} value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} required />
        </div>
        <ErrorNote message={error} />
        <Button type="submit" disabled={busy}>{busy ? t.loading : t.addLaw}</Button>
      </form>
    </Card>
  );
}

function PortalSection() {
  const { t } = useI18n();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactId, setContactId] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiGet<Contact[]>("/contacts").then(setContacts).catch(() => {});
  }, []);

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    try {
      await apiPost("/portal/invite", { contact_id: contactId, password });
      setMessage("✓");
      setPassword("");
      apiGet<Contact[]>("/contacts").then(setContacts).catch(() => {});
    } catch (err) {
      setMessage(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-5 space-y-4">
      <h2 className="font-semibold">{t.portalAccess}</h2>
      <form onSubmit={invite} className="flex gap-3 items-end flex-wrap">
        <div className="flex-1 min-w-56">
          <Label>{t.client}</Label>
          <Select value={contactId} onChange={(e) => setContactId(e.target.value)} required>
            <option value="">—</option>
            {contacts
              .filter((c) => c.email)
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.display_name} {c.portal_enabled ? "✓" : ""}
                </option>
              ))}
          </Select>
        </div>
        <div className="w-48">
          <Label>{t.password}</Label>
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        </div>
        <Button type="submit">{t.invitePortal}</Button>
        {message && <span className="text-sm">{message}</span>}
      </form>
    </Card>
  );
}

/** Public marketplace directory profile: opt-in visibility, bio, areas. */
function PublicProfileSection({ isNotary = false }: { isNotary?: boolean }) {
  const { t } = useI18n();
  const [profile, setProfile] = useState({
    is_visible: false,
    sos_on_duty: false,
    bio: "",
    practice_areas: [] as string[],
    cities: "",
    languages: [] as string[],
    photo: null as string | null,
    oak_license_no: "",
    consult_fee_eur: "" as string,
    career_start_year: "" as string,
    phone: "",
    sms_case_alerts: false,
  });
  const [flatServices, setFlatServices] = useState<{ title: string; price: string }[]>([]);
  const [verification, setVerification] = useState<{
    status: string;
    note: string | null;
  }>({ status: "none", note: null });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const AREAS = ["civil", "criminal", "family", "commercial", "labor", "administrative", "other"];
  // German offices: German-market languages, no SOS duty (D-034)
  const [isDE, setIsDE] = useState(false);
  useEffect(() => setIsDE(clientCountry() === "DE"), []);
  const LANGS: { code: string; label: string }[] = isDE
    ? [
        { code: "de", label: "Deutsch" },
        { code: "en", label: "English" },
        { code: "tr", label: "Türkçe" },
      ]
    : [
        { code: "sq", label: "Shqip" },
        { code: "sr", label: "Srpski" },
        { code: "tr", label: "Türkçe" },
        { code: "bs", label: "Bosanski" },
        { code: "en", label: "English" },
        { code: "zh", label: "中文" },
      ];

  useEffect(() => {
    apiGet<{
      is_visible: boolean;
      sos_on_duty: boolean;
      bio: string | null;
      practice_areas: string[];
      cities: string[];
      languages: string[];
      photo: string | null;
      oak_license_no: string | null;
      verification_status: string;
      verification_note: string | null;
      consult_fee_eur: number | null;
      career_start_year: number | null;
      phone: string | null;
      sms_case_alerts: boolean;
      flat_services: { title: string; price_eur: number }[];
    }>("/marketplace/profile")
      .then((p) => {
        setFlatServices(
          (p.flat_services || []).map((s) => ({ title: s.title, price: String(s.price_eur) }))
        );
        setProfile({
          is_visible: p.is_visible,
          sos_on_duty: p.sos_on_duty,
          bio: p.bio || "",
          practice_areas: p.practice_areas,
          cities: p.cities.join(", "),
          languages: p.languages,
          photo: p.photo,
          oak_license_no: p.oak_license_no || "",
          consult_fee_eur: p.consult_fee_eur == null ? "" : String(p.consult_fee_eur),
          career_start_year: p.career_start_year == null ? "" : String(p.career_start_year),
          phone: p.phone || "",
          sms_case_alerts: p.sms_case_alerts,
        });
        setVerification({ status: p.verification_status, note: p.verification_note });
      })
      .catch(() => {});
  }, []);

  function toggle(list: string[], value: string): string[] {
    return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      const p = await apiPut<{ verification_status: string; verification_note: string | null }>(
        "/marketplace/profile",
        {
          is_visible: profile.is_visible,
          sos_on_duty: profile.sos_on_duty,
          bio: profile.bio || null,
          practice_areas: profile.practice_areas,
          cities: profile.cities.split(",").map((c) => c.trim()).filter(Boolean),
          languages: profile.languages,
          photo: profile.photo,
          oak_license_no: profile.oak_license_no.trim() || null,
          consult_fee_eur: profile.consult_fee_eur === "" ? null : Number(profile.consult_fee_eur),
          career_start_year:
            profile.career_start_year === "" ? null : Number(profile.career_start_year),
          phone: profile.phone.trim() || null,
          sms_case_alerts: profile.sms_case_alerts,
          flat_services: flatServices
            .filter((s) => s.title.trim().length >= 3 && Number(s.price) >= 1)
            .map((s) => ({ title: s.title.trim(), price_eur: Number(s.price) })),
        }
      );
      setVerification({ status: p.verification_status, note: p.verification_note });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  function onPhotoFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || file.size > 200 * 1024) return;
    const reader = new FileReader();
    reader.onload = () => setProfile((p) => ({ ...p, photo: reader.result as string }));
    reader.readAsDataURL(file);
  }

  return (
    <Card id="public-profile" className="p-5 space-y-4 scroll-mt-4">
      <div>
        <h2 className="font-semibold">{t.mkPublicProfile}</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          {isNotary ? t.mkPublicProfileHintNotary : t.mkPublicProfileHint}
        </p>
      </div>
      <form onSubmit={save} className="space-y-4">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={profile.is_visible}
            onChange={(e) => setProfile({ ...profile, is_visible: e.target.checked })}
            className="accent-indigo-600"
          />
          {isNotary ? t.mkVisibleInNotaryDirectory : t.mkVisibleInDirectory}
        </label>
        {!isNotary && !isDE && (
        <label className="flex items-center gap-2 text-sm cursor-pointer" title={t.mkSosDutyHint}>
          <input
            type="checkbox"
            checked={profile.sos_on_duty}
            onChange={(e) => setProfile({ ...profile, sos_on_duty: e.target.checked })}
            className="accent-red-600"
          />
          {t.mkSosDuty}
        </label>
        )}
        <div>
          <div className="flex items-center gap-2">
            <Label>{isNotary ? t.mkOnkLicense : t.mkOakLicense}</Label>
            <span
              className={`text-[11px] font-semibold rounded-full px-2 py-0.5 ${
                verification.status === "verified"
                  ? "bg-emerald-100 text-emerald-700"
                  : verification.status === "pending"
                    ? "bg-amber-100 text-amber-700"
                    : verification.status === "rejected"
                      ? "bg-red-100 text-red-700"
                      : "bg-slate-100 text-slate-600"
              }`}
            >
              {verification.status === "verified"
                ? t.mkVerifVerified
                : verification.status === "pending"
                  ? t.mkVerifPending
                  : verification.status === "rejected"
                    ? t.mkVerifRejected
                    : t.mkVerifNone}
            </span>
          </div>
          <Input
            value={profile.oak_license_no}
            onChange={(e) => setProfile({ ...profile, oak_license_no: e.target.value })}
            placeholder="p.sh. 1234"
            maxLength={64}
          />
          <p className="text-xs text-slate-500 mt-1">
            {isNotary ? t.mkOnkLicenseHint : t.mkOakLicenseHint}
          </p>
          {verification.status === "pending" && (
            <p className="text-xs text-amber-700 mt-1">{t.mkVerifPendingNote}</p>
          )}
          {verification.status === "rejected" && (
            <p className="text-xs text-red-700 mt-1">
              {t.mkVerifRejectedNote}
              {verification.note ? ` (${verification.note})` : ""}
            </p>
          )}
        </div>
        {/* Notary fees are fixed by administrative instruction (UA 02/2012) —
            no custom consultation fee, no marketplace SMS alerts */}
        {!isNotary && (
        <div>
          <Label>{t.mkConsultFee}</Label>
          <Input
            type="number"
            min={0}
            max={10000}
            value={profile.consult_fee_eur}
            onChange={(e) => setProfile({ ...profile, consult_fee_eur: e.target.value })}
            placeholder="p.sh. 30"
          />
          <p className="text-xs text-slate-500 mt-1">{t.mkConsultFeeHint}</p>
        </div>
        )}
        {!isNotary && (
        <div>
          <Label>{t.fsTitle}</Label>
          <p className="text-xs text-slate-500 mb-2">{t.fsHint}</p>
          <div className="space-y-2">
            {flatServices.map((s, i) => (
              <div key={i} className="flex gap-2 items-center">
                <Input
                  value={s.title}
                  onChange={(e) =>
                    setFlatServices((prev) =>
                      prev.map((x, j) => (j === i ? { ...x, title: e.target.value } : x))
                    )
                  }
                  placeholder={t.fsServicePlaceholder}
                  maxLength={120}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={1}
                  max={10000}
                  value={s.price}
                  onChange={(e) =>
                    setFlatServices((prev) =>
                      prev.map((x, j) => (j === i ? { ...x, price: e.target.value } : x))
                    )
                  }
                  placeholder="EUR"
                  className="w-24"
                />
                <button
                  type="button"
                  onClick={() => setFlatServices((prev) => prev.filter((_, j) => j !== i))}
                  className="text-slate-400 hover:text-red-600 text-lg leading-none px-1"
                  aria-label={t.remove}
                >
                  ×
                </button>
              </div>
            ))}
            {flatServices.length < 10 && (
              <button
                type="button"
                onClick={() => setFlatServices((prev) => [...prev, { title: "", price: "" }])}
                className="text-xs text-indigo-600 hover:underline font-medium"
              >
                + {t.fsAdd}
              </button>
            )}
          </div>
        </div>
        )}
        <div>
          <Label>{t.mkCareerStart}</Label>
          <Input
            type="number"
            min={1950}
            max={new Date().getFullYear()}
            value={profile.career_start_year}
            onChange={(e) => setProfile({ ...profile, career_start_year: e.target.value })}
            placeholder="p.sh. 2010"
          />
          <p className="text-xs text-slate-500 mt-1">{t.mkCareerStartHint}</p>
        </div>
        <div>
          <Label>{t.mkSmsPhone}</Label>
          <Input
            type="tel"
            value={profile.phone}
            onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            placeholder="+383 44 000 000"
            maxLength={64}
          />
          {!isNotary && (
            <>
              <label className="flex items-center gap-2 text-sm cursor-pointer mt-2">
                <input
                  type="checkbox"
                  checked={profile.sms_case_alerts}
                  onChange={(e) => setProfile({ ...profile, sms_case_alerts: e.target.checked })}
                  className="accent-indigo-600"
                />
                {t.mkSmsAlerts}
              </label>
              <p className="text-xs text-slate-500 mt-1">{t.mkSmsHint}</p>
            </>
          )}
        </div>
        <div>
          <Label>{t.mkBio}</Label>
          <Textarea
            rows={3}
            value={profile.bio}
            onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
            maxLength={4000}
          />
        </div>
        {!isNotary && (
        <div>
          <Label>{t.practiceArea}</Label>
          <div className="flex flex-wrap gap-2">
            {AREAS.map((a) => (
              <button
                key={a}
                type="button"
                onClick={() =>
                  setProfile({ ...profile, practice_areas: toggle(profile.practice_areas, a) })
                }
                className={`text-xs rounded-full px-3 py-1 border ${
                  profile.practice_areas.includes(a)
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-slate-600 border-slate-300"
                }`}
              >
                {t[a as keyof typeof t] as string}
              </button>
            ))}
          </div>
        </div>
        )}
        <div>
          <Label>{t.mkCities}</Label>
          <Input
            value={profile.cities}
            onChange={(e) => setProfile({ ...profile, cities: e.target.value })}
            placeholder={isDE ? "Berlin, Hamburg" : "Prishtinë, Prizren"}
          />
        </div>
        <div>
          <Label>{t.mkLanguagesLabel}</Label>
          <div className="flex flex-wrap gap-2">
            {LANGS.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() =>
                  setProfile({ ...profile, languages: toggle(profile.languages, l.code) })
                }
                className={`text-xs rounded-full px-3 py-1 border ${
                  profile.languages.includes(l.code)
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-slate-600 border-slate-300"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <Label>{t.mkPhoto}</Label>
          <div className="flex items-center gap-3">
            {profile.photo && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={profile.photo} alt="" className="h-12 w-12 rounded-full object-cover" />
            )}
            <input type="file" accept="image/*" onChange={onPhotoFile} className="text-xs" />
          </div>
        </div>
        <ErrorNote message={error} />
        <div className="flex items-center gap-3">
          <Button type="submit">{t.save}</Button>
          {saved && <span className="text-sm text-emerald-600">{t.mkProfileSaved}</span>}
        </div>
      </form>
    </Card>
  );
}

/** Lawyer-brings-lawyer program: share link + count of referred offices. */
/** Office memory (Vincent-Skills-lite): standing preferences Ava applies on
 * every assistant request — drafting style, citation habits, standard notes. */
function AvaStyleSection() {
  const { t } = useI18n();
  const [style, setStyle] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<{ style: string | null }>("/assistant/style")
      .then((d) => setStyle(d.style || ""))
      .catch(() => {});
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      await apiPut("/assistant/style", { style });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-5 space-y-3">
      <div>
        <h2 className="font-semibold">{t.avaStyleTitle}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.avaStyleHint}</p>
      </div>
      <form onSubmit={save} className="space-y-3">
        <Textarea
          rows={4}
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          maxLength={2000}
          placeholder={t.avaStylePlaceholder}
        />
        <ErrorNote message={error} />
        <div className="flex items-center gap-3">
          <Button type="submit">{t.save}</Button>
          {saved && <span className="text-sm text-emerald-600">{t.saved}</span>}
        </div>
      </form>
    </Card>
  );
}

function ReferralSection() {
  const { t } = useI18n();
  const [data, setData] = useState<{ code: string; url: string; referred_count: number } | null>(
    null
  );
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    apiGet<{ code: string; url: string; referred_count: number }>("/marketplace/referral")
      .then(setData)
      .catch(() => {});
  }, []);

  if (!data) return null;
  return (
    <Card className="p-5 space-y-3">
      <div>
        <h2 className="font-semibold">{t.refTitle}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.refHint}</p>
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        <code className="text-sm bg-slate-100 rounded-lg px-3 py-2 break-all">{data.url}</code>
        <Button
          type="button"
          onClick={() => {
            navigator.clipboard.writeText(data.url).then(() => {
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            });
          }}
        >
          {copied ? t.refCopied : t.refCopy}
        </Button>
      </div>
      <p className="text-sm text-slate-600">
        {t.refCount.replace("{n}", String(data.referred_count))}
      </p>
    </Card>
  );
}

interface BookingWindow {
  day: number;
  start: string;
  end: string;
}

/** Consultation booking (Phase 4): weekly availability windows; citizens
 * reserve 30-minute slots from the public directory. */
function BookingSection() {
  const { t, locale } = useI18n();
  const [enabled, setEnabled] = useState(false);
  const [hasProfile, setHasProfile] = useState(true);
  const [windows, setWindows] = useState<BookingWindow[]>([]);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<{ enabled: boolean; slots: BookingWindow[]; has_profile: boolean }>(
      "/marketplace/booking-settings"
    )
      .then((r) => {
        setEnabled(r.enabled);
        setWindows(r.slots);
        setHasProfile(r.has_profile);
      })
      .catch(() => {});
  }, []);

  // 2024-01-01 is a Monday; render localized weekday names
  const dayName = (day: number) =>
    new Date(Date.UTC(2024, 0, 1 + day)).toLocaleDateString(locale, {
      weekday: "long",
      timeZone: "UTC",
    });

  function windowFor(day: number): BookingWindow | undefined {
    return windows.find((w) => w.day === day);
  }

  function toggleDay(day: number) {
    setWindows((prev) =>
      prev.some((w) => w.day === day)
        ? prev.filter((w) => w.day !== day)
        : [...prev, { day, start: "09:00", end: "16:00" }]
    );
  }

  function setTime(day: number, field: "start" | "end", value: string) {
    setWindows((prev) => prev.map((w) => (w.day === day ? { ...w, [field]: value } : w)));
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      await apiPut("/marketplace/booking-settings", { enabled, slots: windows });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  return (
    <Card className="p-6 space-y-4">
      <div>
        <h2 className="font-semibold">{t.bkTitle}</h2>
        <p className="text-xs text-slate-500 mt-1">{t.bkSettingsHint}</p>
      </div>
      {!hasProfile ? (
        <p className="text-sm bg-amber-50 text-amber-800 rounded-lg p-3">{t.bkNeedProfile}</p>
      ) : (
        <form onSubmit={save} className="space-y-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="rounded border-slate-300"
            />
            {t.bkEnable}
          </label>
          {enabled && (
            <div className="space-y-2">
              {[0, 1, 2, 3, 4, 5, 6].map((day) => {
                const w = windowFor(day);
                return (
                  <div key={day} className="flex items-center gap-3 flex-wrap">
                    <label className="flex items-center gap-2 text-sm w-36">
                      <input
                        type="checkbox"
                        checked={!!w}
                        onChange={() => toggleDay(day)}
                        className="rounded border-slate-300"
                      />
                      <span className="capitalize">{dayName(day)}</span>
                    </label>
                    {w && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-xs text-slate-400">{t.bkFrom}</span>
                        <Input
                          type="time"
                          value={w.start}
                          onChange={(e) => setTime(day, "start", e.target.value)}
                          className="!w-28"
                        />
                        <span className="text-xs text-slate-400">{t.bkTo}</span>
                        <Input
                          type="time"
                          value={w.end}
                          onChange={(e) => setTime(day, "end", e.target.value)}
                          className="!w-28"
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          <ErrorNote message={error} />
          <div className="flex items-center gap-3">
            <Button type="submit">{t.save}</Button>
            {saved && <span className="text-sm text-emerald-600">✓</span>}
          </div>
        </form>
      )}
    </Card>
  );
}
