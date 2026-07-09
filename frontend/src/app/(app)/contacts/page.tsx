"use client";

import { useCallback, useEffect, useState } from "react";
import { apiDownload, apiGet, apiPost, apiPut } from "@/lib/api";
import { LOCALES } from "@/lib/dictionaries";
import { useI18n } from "@/lib/i18n";
import { ConsentRecord, Contact } from "@/lib/types";
import { Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner } from "@/components/ui";

export default function ContactsPage() {
  const { t } = useI18n();
  const [contacts, setContacts] = useState<Contact[] | null>(null);
  const [q, setQ] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [open, setOpen] = useState<Contact | null>(null);
  const [form, setForm] = useState({
    kind: "person",
    display_name: "",
    email: "",
    phone: "",
    address: "",
    locale: "",
  });

  const load = useCallback(() => {
    apiGet<Contact[]>(`/contacts${q ? `?q=${encodeURIComponent(q)}` : ""}`)
      .then(setContacts)
      .catch(() => {});
  }, [q]);

  useEffect(() => {
    load();
  }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    await apiPost("/contacts", {
      ...form,
      email: form.email || null,
      phone: form.phone || null,
      address: form.address || null,
      locale: form.locale || null,
    });
    setShowNew(false);
    setForm({ kind: "person", display_name: "", email: "", phone: "", address: "", locale: "" });
    load();
  }

  if (open) {
    return (
      <ContactDetail
        contact={open}
        onClose={() => {
          setOpen(null);
          load();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t.contacts}</h1>
        <Button onClick={() => setShowNew(!showNew)}>{t.newContact}</Button>
      </div>

      {showNew && (
        <Card className="p-5">
          <form onSubmit={create} className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>{t.name}</Label>
              <Input value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} required />
            </div>
            <div>
              <Label>{t.category}</Label>
              <Select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
                <option value="person">{t.person}</option>
                <option value="organization">{t.organization}</option>
              </Select>
            </div>
            <div>
              <Label>{t.email}</Label>
              <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <Label>{t.phone}</Label>
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div className="md:col-span-2">
              <Label>{t.address}</Label>
              <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </div>
            <div className="md:col-span-2">
              <Label>{t.communicationLanguage}</Label>
              <Select value={form.locale} onChange={(e) => setForm({ ...form, locale: e.target.value })}>
                <option value="">{t.firmDefault}</option>
                {LOCALES.map((l) => (
                  <option key={l.code} value={l.code}>{l.label}</option>
                ))}
              </Select>
              <p className="mt-1 text-xs text-slate-400">{t.communicationLanguageHint}</p>
            </div>
            <div className="md:col-span-2 flex gap-2">
              <Button type="submit">{t.save}</Button>
              <Button type="button" variant="secondary" onClick={() => setShowNew(false)}>{t.cancel}</Button>
            </div>
          </form>
        </Card>
      )}

      <Input placeholder={t.search} value={q} onChange={(e) => setQ(e.target.value)} className="max-w-sm" />

      {contacts === null ? (
        <Spinner />
      ) : (
        <>
          <div className="md:hidden space-y-2">
            {contacts.map((c) => (
              <button
                key={c.id}
                onClick={() => setOpen(c)}
                className="w-full text-left bg-white rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-sm">{c.display_name}</p>
                  <div className="flex items-center gap-1">
                    {c.anonymized_at && <Badge status="closed" label={t.anonymizedLabel} />}
                    {c.portal_enabled && <Badge status="open" label="✓" />}
                  </div>
                </div>
                <p className="mt-0.5 text-xs text-slate-500">
                  {c.email || "—"}{c.phone ? ` · ${c.phone}` : ""}
                </p>
              </button>
            ))}
          </div>
          <Card className="hidden md:block">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                    <th className="px-4 py-3">{t.name}</th>
                    <th className="px-4 py-3">{t.email}</th>
                    <th className="px-4 py-3">{t.phone}</th>
                    <th className="px-4 py-3">{t.communicationLanguage}</th>
                    <th className="px-4 py-3">{t.riskLevel}</th>
                    <th className="px-4 py-3">{t.portalAccess}</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts.map((c) => (
                    <tr
                      key={c.id}
                      className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
                      onClick={() => setOpen(c)}
                    >
                      <td className="px-4 py-3 font-medium">
                        {c.display_name}
                        {c.anonymized_at && (
                          <span className="ml-2 text-xs text-slate-400">({t.anonymizedLabel})</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{c.email || "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{c.phone || "—"}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {LOCALES.find((l) => l.code === c.locale)?.label || "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {c.risk_level === "high" ? (
                          <Badge status="urgent" label={t.riskHigh} />
                        ) : c.risk_level === "low" ? (
                          t.riskLow
                        ) : c.risk_level === "standard" ? (
                          t.riskStandard
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {c.portal_enabled ? <Badge status="open" label="✓" /> : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

const CONSENT_KINDS = ["portal_tos", "email", "sms", "ai_processing"] as const;

function ContactDetail({ contact, onClose }: { contact: Contact; onClose: () => void }) {
  const { t } = useI18n();
  const [c, setC] = useState<Contact>(contact);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSaved(false);
    try {
      const updated = await apiPut<Contact>(`/contacts/${c.id}`, {
        kind: c.kind,
        display_name: c.display_name,
        national_id: c.national_id || null,
        email: c.email || null,
        phone: c.phone || null,
        address: c.address || null,
        notes: c.notes || null,
        locale: c.locale || null,
        id_doc_type: c.id_doc_type || null,
        id_doc_number: c.id_doc_number || null,
        id_verified_on: c.id_verified_on || null,
        risk_level: c.risk_level || null,
        is_pep: c.is_pep,
        beneficial_owner: c.beneficial_owner || null,
      });
      setC(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button onClick={onClose} className="text-sm text-indigo-600 hover:underline">
            ← {t.contacts}
          </button>
          <h1 className="text-2xl font-bold">
            {c.display_name}
            {c.anonymized_at && (
              <span className="ml-2 text-sm font-normal text-slate-400">({t.anonymizedLabel})</span>
            )}
          </h1>
        </div>
      </div>

      <Card className="p-5">
        <form onSubmit={save} className="grid md:grid-cols-2 gap-4">
          <div>
            <Label>{t.name}</Label>
            <Input value={c.display_name} onChange={(e) => setC({ ...c, display_name: e.target.value })} required />
          </div>
          <div>
            <Label>{t.communicationLanguage}</Label>
            <Select value={c.locale || ""} onChange={(e) => setC({ ...c, locale: e.target.value || null })}>
              <option value="">{t.firmDefault}</option>
              {LOCALES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </Select>
          </div>
          <div>
            <Label>{t.email}</Label>
            <Input type="email" value={c.email || ""} onChange={(e) => setC({ ...c, email: e.target.value })} />
          </div>
          <div>
            <Label>{t.phone}</Label>
            <Input value={c.phone || ""} onChange={(e) => setC({ ...c, phone: e.target.value })} />
          </div>
          <div className="md:col-span-2">
            <Label>{t.address}</Label>
            <Input value={c.address || ""} onChange={(e) => setC({ ...c, address: e.target.value })} />
          </div>

          <div className="md:col-span-2 pt-2 border-t border-slate-100">
            <h3 className="font-semibold text-sm">{t.kycTitle}</h3>
          </div>
          <div>
            <Label>{t.idDocType}</Label>
            <Select value={c.id_doc_type || ""} onChange={(e) => setC({ ...c, id_doc_type: e.target.value || null })}>
              <option value="">—</option>
              <option value="id_card">{t.idTypeId}</option>
              <option value="passport">{t.idTypePassport}</option>
              <option value="other">{t.idTypeOther}</option>
            </Select>
          </div>
          <div>
            <Label>{t.idDocNumber}</Label>
            <Input value={c.id_doc_number || ""} onChange={(e) => setC({ ...c, id_doc_number: e.target.value })} />
          </div>
          <div>
            <Label>{t.idVerifiedOn}</Label>
            <Input
              type="date"
              value={c.id_verified_on || ""}
              onChange={(e) => setC({ ...c, id_verified_on: e.target.value || null })}
            />
          </div>
          <div>
            <Label>{t.riskLevel}</Label>
            <Select value={c.risk_level || ""} onChange={(e) => setC({ ...c, risk_level: e.target.value || null })}>
              <option value="">—</option>
              <option value="low">{t.riskLow}</option>
              <option value="standard">{t.riskStandard}</option>
              <option value="high">{t.riskHigh}</option>
            </Select>
          </div>
          <div>
            <Label>{t.beneficialOwner}</Label>
            <Input value={c.beneficial_owner || ""} onChange={(e) => setC({ ...c, beneficial_owner: e.target.value })} />
          </div>
          <div className="flex items-end pb-2">
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={c.is_pep}
                onChange={(e) => setC({ ...c, is_pep: e.target.checked })}
                className="accent-indigo-600"
              />
              {t.pepLabel}
            </label>
          </div>

          <div className="md:col-span-2 flex items-center gap-3">
            <Button type="submit" disabled={busy}>{t.save}</Button>
            {saved && <span className="text-sm text-emerald-600">✓ {t.saved}</span>}
            <ErrorNote message={error} />
          </div>
        </form>
      </Card>

      <ConsentsCard contactId={c.id} />
      <PrivacyCard contact={c} onChanged={setC} />
    </div>
  );
}

function ConsentsCard({ contactId }: { contactId: string }) {
  const { t } = useI18n();
  const [records, setRecords] = useState<ConsentRecord[] | null>(null);
  const [busyKind, setBusyKind] = useState<string | null>(null);

  const labels: Record<string, string> = {
    portal_tos: t.consentPortalTos,
    email: t.consentEmail,
    sms: t.consentSms,
    ai_processing: t.consentAi,
  };

  const load = useCallback(() => {
    apiGet<ConsentRecord[]>(`/contacts/${contactId}/consents`).then(setRecords).catch(() => {});
  }, [contactId]);

  useEffect(() => {
    load();
  }, [load]);

  async function toggle(kind: string, granted: boolean) {
    setBusyKind(kind);
    try {
      const updated = await apiPost<ConsentRecord[]>(`/contacts/${contactId}/consents`, {
        kind,
        granted,
      });
      setRecords(updated);
    } finally {
      setBusyKind(null);
    }
  }

  if (records === null) return <Spinner />;

  return (
    <Card className="p-5 space-y-3">
      <div>
        <h3 className="font-semibold text-sm">{t.consents}</h3>
        <p className="text-xs text-slate-400 mt-0.5">{t.consentSmsHint}</p>
      </div>
      <div className="divide-y divide-slate-100">
        {CONSENT_KINDS.map((kind) => {
          const active = records.find((r) => r.kind === kind && !r.revoked_at);
          return (
            <div key={kind} className="flex items-center justify-between gap-3 py-2.5">
              <div>
                <p className="text-sm font-medium">{labels[kind]}</p>
                {active ? (
                  <p className="text-xs text-emerald-600">
                    {t.consentGranted} · {new Date(active.granted_at).toLocaleDateString()} · {active.method}
                  </p>
                ) : (
                  <p className="text-xs text-slate-400">{t.consentNotGranted}</p>
                )}
              </div>
              <Button
                variant="secondary"
                disabled={busyKind === kind}
                onClick={() => toggle(kind, !active)}
              >
                {active ? t.revokeConsent : t.grantConsent}
              </Button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function PrivacyCard({ contact, onChanged }: { contact: Contact; onChanged: (c: Contact) => void }) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  async function exportZip() {
    setBusy(true);
    setError("");
    try {
      const ok = await apiDownload(`/contacts/${contact.id}/export`, `contact-${contact.id}.zip`);
      if (!ok) setError(t.error);
    } finally {
      setBusy(false);
    }
  }

  async function erase() {
    if (!window.confirm(t.eraseConfirm)) return;
    setBusy(true);
    setError("");
    try {
      await apiPost(`/contacts/${contact.id}/erasure`);
      const updated = await apiGet<Contact>(`/contacts/${contact.id}`);
      onChanged(updated);
      setDone(t.contactAnonymized);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 space-y-3">
      <div>
        <h3 className="font-semibold text-sm">{t.privacyTitle}</h3>
        <p className="text-xs text-slate-400 mt-0.5">{t.eraseContactHint}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={exportZip} disabled={busy}>
          {t.exportContactData}
        </Button>
        {!contact.anonymized_at && (
          <Button variant="danger" onClick={erase} disabled={busy}>
            {t.eraseContact}
          </Button>
        )}
      </div>
      {done && <p className="text-sm text-emerald-600">✓ {done}</p>}
      <ErrorNote message={error} />
    </Card>
  );
}
