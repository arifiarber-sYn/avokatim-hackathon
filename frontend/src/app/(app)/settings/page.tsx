"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
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
      <TwoFASection />
      <CorpusSection />
      <PortalSection />
    </div>
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
