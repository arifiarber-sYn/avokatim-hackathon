"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { LOCALES } from "@/lib/dictionaries";
import { useI18n } from "@/lib/i18n";
import { Contact } from "@/lib/types";
import { Badge, Button, Card, Input, Label, Select, Spinner } from "@/components/ui";

export default function ContactsPage() {
  const { t } = useI18n();
  const [contacts, setContacts] = useState<Contact[] | null>(null);
  const [q, setQ] = useState("");
  const [showNew, setShowNew] = useState(false);
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
              <div key={c.id} className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-sm">{c.display_name}</p>
                  {c.portal_enabled && <Badge status="open" label="✓" />}
                </div>
                <p className="mt-0.5 text-xs text-slate-500">
                  {c.email || "—"}{c.phone ? ` · ${c.phone}` : ""}
                </p>
              </div>
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
                    <th className="px-4 py-3">{t.portalAccess}</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts.map((c) => (
                    <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium">{c.display_name}</td>
                      <td className="px-4 py-3 text-slate-600">{c.email || "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{c.phone || "—"}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {LOCALES.find((l) => l.code === c.locale)?.label || "—"}
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
