"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost, apiUpload } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
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

export default function SettingsPage() {
  const { t } = useI18n();
  return (
    <div className="space-y-8 max-w-3xl">
      <h1 className="text-2xl font-bold">{t.settings}</h1>
      <ProfileSection />
      <FirmSection />
      <PushSection />
      <TeamSection />
      <CalendarFeedSection />
      <PublicIntakeSection />
      <ImportSection />
      <TwoFASection />
      <CorpusSection />
      <PortalSection />
    </div>
  );
}

function FirmSection() {
  const { t } = useI18n();
  const [form, setForm] = useState({
    name: "",
    fiscal_number: "",
    vat_number: "",
    address: "",
    default_vat_rate: "18",
  });
  const [logo, setLogo] = useState<string | null>(null);
  const [require2fa, setRequire2fa] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<{
      name: string;
      fiscal_number: string | null;
      vat_number: string | null;
      address: string | null;
      default_vat_rate: number;
      logo: string | null;
      require_2fa: boolean;
    }>("/firm")
      .then((r) => {
        setForm({
          name: r.name || "",
          fiscal_number: r.fiscal_number || "",
          vat_number: r.vat_number || "",
          address: r.address || "",
          default_vat_rate: String(r.default_vat_rate ?? 18),
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
        default_vat_rate: Number(form.default_vat_rate),
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

  return (
    <Card className="p-5 space-y-3">
      <h2 className="font-semibold">{t.pushNotifications}</h2>
      <p className="text-sm text-slate-500">{t.pushHint}</p>
      {!supported || !serverEnabled ? (
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
      await apiPost("/auth/change-password", {
        current_password: current,
        new_password: next,
      });
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
