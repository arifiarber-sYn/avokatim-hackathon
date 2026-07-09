"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Contact, Matter, PRACTICE_AREAS } from "@/lib/types";
import {
  Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea,
} from "@/components/ui";

export default function MattersPage() {
  const { t } = useI18n();
  const [matters, setMatters] = useState<Matter[] | null>(null);
  const [q, setQ] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    practice_area: "civil",
    client_id: "",
    court_name: "",
    description: "",
  });

  const load = useCallback(() => {
    apiGet<Matter[]>(`/matters${q ? `?q=${encodeURIComponent(q)}` : ""}`)
      .then(setMatters)
      .catch(() => {});
  }, [q]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (showNew) apiGet<Contact[]>("/contacts").then(setContacts).catch(() => {});
  }, [showNew]);

  async function createMatter(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/matters", {
        title: form.title,
        practice_area: form.practice_area,
        client_id: form.client_id || null,
        court_name: form.court_name || null,
        description: form.description || null,
        jurisdiction_code: "XK",
      });
      setShowNew(false);
      setForm({ title: "", practice_area: "civil", client_id: "", court_name: "", description: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  const areaLabel = (a: string) => (t as Record<string, string>)[a] || a;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">{t.matters}</h1>
        <Button onClick={() => setShowNew(!showNew)}>{t.newMatter}</Button>
      </div>

      {showNew && (
        <Card className="p-5">
          <form onSubmit={createMatter} className="grid md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Label>{t.title}</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
            </div>
            <div>
              <Label>{t.practiceArea}</Label>
              <Select
                value={form.practice_area}
                onChange={(e) => setForm({ ...form, practice_area: e.target.value })}
              >
                {PRACTICE_AREAS.map((a) => (
                  <option key={a} value={a}>{areaLabel(a)}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t.client}</Label>
              <Select value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })}>
                <option value="">—</option>
                {contacts.map((c) => (
                  <option key={c.id} value={c.id}>{c.display_name}</option>
                ))}
              </Select>
            </div>
            <div className="md:col-span-2">
              <Label>{t.courtName}</Label>
              <Input value={form.court_name} onChange={(e) => setForm({ ...form, court_name: e.target.value })} />
            </div>
            <div className="md:col-span-2">
              <Label>{t.description}</Label>
              <Textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="md:col-span-2 flex gap-2">
              <ErrorNote message={error} />
              <Button type="submit">{t.save}</Button>
              <Button type="button" variant="secondary" onClick={() => setShowNew(false)}>{t.cancel}</Button>
            </div>
          </form>
        </Card>
      )}

      <Input placeholder={t.search} value={q} onChange={(e) => setQ(e.target.value)} className="max-w-sm" />

      {matters === null ? (
        <Spinner />
      ) : (
        <>
          {/* Mobile: card list */}
          <div className="md:hidden space-y-2">
            {matters.map((m) => (
              <Link
                key={m.id}
                href={`/matters/${m.id}`}
                className="block bg-white rounded-xl border border-slate-200 p-4 active:bg-slate-50"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-indigo-600">{m.reference}</span>
                  <Badge status={m.status} label={(t as Record<string, string>)[m.status]} />
                </div>
                <p className="mt-1 font-medium text-sm">{m.title}</p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {m.client?.display_name || "—"} · {areaLabel(m.practice_area)}
                </p>
              </Link>
            ))}
          </div>
          {/* Desktop: table */}
          <Card className="hidden md:block">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
                    <th className="px-4 py-3">{t.reference}</th>
                    <th className="px-4 py-3">{t.title}</th>
                    <th className="px-4 py-3">{t.client}</th>
                    <th className="px-4 py-3">{t.practiceArea}</th>
                    <th className="px-4 py-3">{t.status}</th>
                  </tr>
                </thead>
                <tbody>
                  {matters.map((m) => (
                    <tr key={m.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-xs">
                        <Link href={`/matters/${m.id}`} className="text-indigo-600 hover:underline">
                          {m.reference}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <Link href={`/matters/${m.id}`} className="hover:underline">{m.title}</Link>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{m.client?.display_name || "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{areaLabel(m.practice_area)}</td>
                      <td className="px-4 py-3">
                        <Badge status={m.status} label={(t as Record<string, string>)[m.status]} />
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
