"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
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
      <TeamSection />
      <CalendarFeedSection />
      <PublicIntakeSection />
      <TwoFASection />
      <CorpusSection />
      <PortalSection />
    </div>
  );
}

interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

function TeamSection() {
  const { t } = useI18n();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "lawyer" });
  const [error, setError] = useState("");

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
    try {
      await apiPost("/team", form);
      setForm({ full_name: "", email: "", password: "", role: "lawyer" });
      load();
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
              <button
                onClick={() => toggleActive(m)}
                className={`text-xs hover:underline ${m.is_active ? "text-red-600" : "text-emerald-600"}`}
              >
                {m.is_active ? t.deactivate : t.activate}
              </button>
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
          <Label>{t.password}</Label>
          <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={10} />
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
          <Button type="submit">{t.addMember}</Button>
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
    </Card>
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
