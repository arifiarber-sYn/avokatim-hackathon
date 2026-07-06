"use client";

import { use, useCallback, useEffect, useState } from "react";
import { apiGet, apiPost, apiUpload, getToken } from "@/lib/api";
import { localized, useI18n } from "@/lib/i18n";
import {
  Contact, Deadline, DeadlineRule, Doc, Matter,
} from "@/lib/types";
import {
  Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea,
} from "@/components/ui";

interface Party {
  id: string;
  role: string;
  contact: Contact;
}

interface Note {
  id: string;
  body: string;
  created_at: string;
}

const PARTY_ROLES = ["client", "opposing_party", "opposing_counsel", "witness", "judge", "expert", "other"];

export default function MatterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const [matter, setMatter] = useState<Matter | null>(null);
  const [tab, setTab] = useState<"overview" | "parties" | "documents" | "deadlines" | "notes" | "ai">("overview");

  useEffect(() => {
    apiGet<Matter>(`/matters/${id}`).then(setMatter).catch(() => {});
  }, [id]);

  if (!matter) return <Spinner />;

  const tabs = [
    ["overview", t.overview],
    ["parties", t.parties],
    ["documents", t.documents],
    ["deadlines", t.deadlines],
    ["notes", t.notes],
    ["ai", t.assistant],
  ] as const;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">{matter.title}</h1>
          <Badge status={matter.status} label={(t as Record<string, string>)[matter.status]} />
        </div>
        <p className="text-sm text-slate-500 font-mono mt-1">{matter.reference}</p>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && <Overview matter={matter} />}
      {tab === "parties" && <Parties matterId={id} />}
      {tab === "documents" && <Documents matterId={id} />}
      {tab === "deadlines" && <Deadlines matterId={id} practiceArea={matter.practice_area} />}
      {tab === "notes" && <Notes matterId={id} />}
      {tab === "ai" && <MatterAI matterId={id} />}
    </div>
  );

  function Overview({ matter }: { matter: Matter }) {
    const rows = [
      [t.client, matter.client?.display_name],
      [t.practiceArea, (t as Record<string, string>)[matter.practice_area]],
      [t.courtName, matter.court_name],
      [t.courtCaseNumber, matter.court_case_number],
      [t.date, matter.opened_on],
    ];
    return (
      <Card className="p-5 space-y-3">
        {rows.map(([label, value]) => (
          <div key={label as string} className="flex text-sm">
            <span className="w-48 text-slate-500">{label}</span>
            <span>{value || "—"}</span>
          </div>
        ))}
        {matter.description && (
          <div className="pt-3 border-t border-slate-100 text-sm whitespace-pre-wrap">
            {matter.description}
          </div>
        )}
      </Card>
    );
  }
}

function Parties({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [parties, setParties] = useState<Party[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactId, setContactId] = useState("");
  const [role, setRole] = useState("opposing_party");

  const load = useCallback(() => {
    apiGet<Party[]>(`/matters/${matterId}/parties`).then(setParties).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    apiGet<Contact[]>("/contacts").then(setContacts).catch(() => {});
  }, [load]);

  async function addParty(e: React.FormEvent) {
    e.preventDefault();
    if (!contactId) return;
    await apiPost(`/matters/${matterId}/parties`, { contact_id: contactId, role });
    setContactId("");
    load();
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <form onSubmit={addParty} className="flex gap-3 items-end flex-wrap">
          <div className="flex-1 min-w-48">
            <Label>{t.contacts}</Label>
            <Select value={contactId} onChange={(e) => setContactId(e.target.value)}>
              <option value="">—</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>{c.display_name}</option>
              ))}
            </Select>
          </div>
          <div className="w-48">
            <Label>{t.role}</Label>
            <Select value={role} onChange={(e) => setRole(e.target.value)}>
              {PARTY_ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </Select>
          </div>
          <Button type="submit">{t.addParty}</Button>
        </form>
      </Card>
      <Card>
        <div className="divide-y divide-slate-100">
          {parties.map((p) => (
            <div key={p.id} className="flex justify-between items-center px-4 py-3 text-sm">
              <div>
                <p className="font-medium">{p.contact.display_name}</p>
                <p className="text-xs text-slate-500">{p.contact.phone || p.contact.email || ""}</p>
              </div>
              <Badge status="open" label={p.role} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Documents({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<Doc[]>(`/matters/${matterId}/documents`).then(setDocs).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
  }, [load]);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      await apiUpload(`/matters/${matterId}/documents`, form);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  async function download(doc: Doc) {
    const res = await fetch(`/api/documents/${doc.id}/download`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = doc.filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="cursor-pointer">
          <span className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 inline-block">
            {busy ? t.loading : t.upload}
          </span>
          <input type="file" className="hidden" onChange={upload} disabled={busy} />
        </label>
        <ErrorNote message={error} />
      </div>
      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
              <th className="px-4 py-3">{t.name}</th>
              <th className="px-4 py-3">{t.version}</th>
              <th className="px-4 py-3">OCR</th>
              <th className="px-4 py-3">{t.uploaded}</th>
              <th className="px-4 py-3">{t.actions}</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-b border-slate-100">
                <td className="px-4 py-3">{d.filename}</td>
                <td className="px-4 py-3">v{d.version}</td>
                <td className="px-4 py-3 text-xs text-slate-500">
                  {d.has_text ? "✓" : d.ocr_status}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {new Date(d.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => download(d)} className="text-indigo-600 hover:underline text-xs">
                    {t.download}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function Deadlines({ matterId, practiceArea }: { matterId: string; practiceArea: string }) {
  const { t, locale } = useI18n();
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [rules, setRules] = useState<DeadlineRule[]>([]);
  const [mode, setMode] = useState<"rule" | "manual">("rule");
  const [ruleId, setRuleId] = useState("");
  const [triggerDate, setTriggerDate] = useState("");
  const [manualTitle, setManualTitle] = useState("");
  const [manualDate, setManualDate] = useState("");
  const [manualKind, setManualKind] = useState("deadline");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<Deadline[]>(`/matters/${matterId}/deadlines`).then(setDeadlines).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    apiGet<DeadlineRule[]>(`/jurisdictions/XK/deadline-rules`).then(setRules).catch(() => {});
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (mode === "rule") {
        await apiPost(`/matters/${matterId}/deadlines/from-rule`, {
          rule_id: ruleId,
          trigger_date: triggerDate,
        });
      } else {
        await apiPost(`/matters/${matterId}/deadlines`, {
          title: manualTitle,
          due_at: new Date(manualDate).toISOString(),
          kind: manualKind,
        });
      }
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function markDone(id: string) {
    await fetch(`/api/deadlines/${id}/status?new_status=done`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    load();
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex gap-2 mb-3">
          <Button variant={mode === "rule" ? "primary" : "secondary"} onClick={() => setMode("rule")}>
            {t.fromRule}
          </Button>
          <Button variant={mode === "manual" ? "primary" : "secondary"} onClick={() => setMode("manual")}>
            {t.manual}
          </Button>
        </div>
        <form onSubmit={add} className="flex gap-3 items-end flex-wrap">
          {mode === "rule" ? (
            <>
              <div className="flex-1 min-w-64">
                <Label>{t.rule}</Label>
                <Select value={ruleId} onChange={(e) => setRuleId(e.target.value)} required>
                  <option value="">—</option>
                  {rules.map((r) => (
                    <option key={r.id} value={r.id}>
                      {localized(r.name, locale)} ({r.days} d — {r.legal_basis})
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>{t.triggerDate}</Label>
                <Input type="date" value={triggerDate} onChange={(e) => setTriggerDate(e.target.value)} required />
              </div>
            </>
          ) : (
            <>
              <div className="flex-1 min-w-48">
                <Label>{t.title}</Label>
                <Input value={manualTitle} onChange={(e) => setManualTitle(e.target.value)} required />
              </div>
              <div>
                <Label>{t.dueDate}</Label>
                <Input type="datetime-local" value={manualDate} onChange={(e) => setManualDate(e.target.value)} required />
              </div>
              <div className="w-36">
                <Label>{t.category}</Label>
                <Select value={manualKind} onChange={(e) => setManualKind(e.target.value)}>
                  <option value="deadline">{t.deadline}</option>
                  <option value="hearing">{t.hearing}</option>
                  <option value="meeting">{t.meeting}</option>
                </Select>
              </div>
            </>
          )}
          <Button type="submit">{t.addDeadline}</Button>
        </form>
        <div className="mt-2">
          <ErrorNote message={error} />
        </div>
      </Card>

      <Card>
        <div className="divide-y divide-slate-100">
          {deadlines.map((d) => {
            const overdue = d.status === "pending" && new Date(d.due_at) < new Date();
            return (
              <div key={d.id} className="flex justify-between items-center px-4 py-3 text-sm">
                <div>
                  <p className="font-medium">{d.title}</p>
                  <p className="text-xs text-slate-500">
                    {d.legal_basis || (t as Record<string, string>)[d.kind]}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={overdue ? "text-red-600 font-semibold" : ""}>
                    {new Date(d.due_at).toLocaleDateString()}
                  </span>
                  <Badge status={d.status} label={(t as Record<string, string>)[d.status]} />
                  {d.status === "pending" && (
                    <button onClick={() => markDone(d.id)} className="text-xs text-emerald-600 hover:underline">
                      {t.markDone}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

function Notes({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [notes, setNotes] = useState<Note[]>([]);
  const [body, setBody] = useState("");

  const load = useCallback(() => {
    apiGet<Note[]>(`/matters/${matterId}/notes`).then(setNotes).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    await apiPost(`/matters/${matterId}/notes`, { body });
    setBody("");
    load();
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <form onSubmit={add} className="space-y-3">
          <Textarea rows={3} value={body} onChange={(e) => setBody(e.target.value)} required placeholder={t.addNote} />
          <Button type="submit">{t.addNote}</Button>
        </form>
      </Card>
      {notes.map((n) => (
        <Card key={n.id} className="p-4">
          <p className="text-xs text-slate-400 mb-1">{new Date(n.created_at).toLocaleString()}</p>
          <p className="text-sm whitespace-pre-wrap">{n.body}</p>
        </Card>
      ))}
    </div>
  );
}

function MatterAI({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [output, setOutput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(action: "summarize" | "hearing") {
    setBusy(true);
    setError("");
    setOutput("");
    try {
      const result =
        action === "summarize"
          ? await apiPost<{ summary: string }>(`/assistant/matters/${matterId}/summarize`)
          : await apiPost<{ summary: string }>(`/assistant/hearing-prep`, { matter_id: matterId });
      setOutput(result.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button onClick={() => run("summarize")} disabled={busy}>{t.summarizeMatter}</Button>
        <Button onClick={() => run("hearing")} disabled={busy} variant="secondary">{t.hearingPrep}</Button>
      </div>
      <ErrorNote message={error} />
      {busy && <p className="text-sm text-slate-500 animate-pulse">{t.thinking}</p>}
      {output && (
        <Card className="p-5">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{output}</p>
        </Card>
      )}
    </div>
  );
}
