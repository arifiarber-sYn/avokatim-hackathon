"use client";

import { use, useCallback, useEffect, useState } from "react";
import { apiDelete, apiDownload, apiGet, apiPatch, apiPost, apiPut, apiStream, apiUpload, getToken } from "@/lib/api";
import { localized, useI18n } from "@/lib/i18n";
import {
  Contact, Deadline, DeadlineRule, Doc, Matter, Task,
} from "@/lib/types";
import {
  Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea,
} from "@/components/ui";
import { MicButton, useVoiceAvailable } from "@/components/voice-controls";

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

interface TeamMember {
  id: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface MatterMsg {
  id: string;
  sender_user_id: string | null;
  sender_contact_id: string | null;
  body: string;
  created_at: string;
}

interface SigRequest {
  id: string;
  document_id: string;
  status: string;
  signer_name: string | null;
  signed_at: string | null;
}

interface ExtractedDeadline {
  title: string;
  kind: string;
  due_date: string | null;
  trigger_date: string | null;
  days: number | null;
  legal_basis: string | null;
  confidence: string;
}

interface DocAiSummary {
  summary: string;
  key_points: string[];
  deadlines: {
    title: string;
    date: string | null;
    days: number | null;
    legal_basis: string | null;
  }[];
}

const PARTY_ROLES = ["client", "opposing_party", "opposing_counsel", "witness", "judge", "expert", "other"];

export default function MatterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, locale } = useI18n();
  const [matter, setMatter] = useState<Matter | null>(null);
  const [tab, setTab] = useState<"overview" | "parties" | "documents" | "deadlines" | "tasks" | "messages" | "notes" | "ai" | "aml">("overview");

  useEffect(() => {
    apiGet<Matter>(`/matters/${id}`).then(setMatter).catch(() => {});
  }, [id]);

  if (!matter) return <Spinner />;

  const tabs = [
    ["overview", t.overview],
    ["parties", t.parties],
    ["documents", t.documents],
    ["deadlines", t.deadlines],
    ["tasks", t.tasksLabel],
    ["messages", t.messages],
    ["notes", t.notes],
    ["ai", t.assistant],
    ["aml", "AML"],
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

      <div className="flex gap-1 border-b border-slate-200 overflow-x-auto whitespace-nowrap -mx-4 px-4 md:mx-0 md:px-0">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`shrink-0 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <>
          <Overview matter={matter} onChanged={setMatter} />
          <DeckungCard matterId={id} />
        </>
      )}
      {tab === "parties" && <Parties matterId={id} />}
      {tab === "documents" && <Documents matterId={id} clientId={matter.client?.id || null} />}
      {tab === "deadlines" && <Deadlines matterId={id} practiceArea={matter.practice_area} />}
      {tab === "tasks" && <Tasks matterId={id} />}
      {tab === "messages" && <Messages matterId={id} />}
      {tab === "notes" && <Notes matterId={id} />}
      {tab === "ai" && <MatterAI matterId={id} />}
      {tab === "aml" && <AmlTab matterId={id} clientId={matter.client?.id || null} />}
    </div>
  );

  function Overview({ matter, onChanged }: { matter: Matter; onChanged: (m: Matter) => void }) {
    const [team, setTeam] = useState<TeamMember[]>([]);
    const [restricted, setRestricted] = useState(matter.restricted);
    const [memberIds, setMemberIds] = useState<Set<string>>(new Set());
    const [accessSaved, setAccessSaved] = useState(false);
    const [inboundEmail, setInboundEmail] = useState<string | null>(null);
    const [emailCopied, setEmailCopied] = useState(false);
    const [isNotary, setIsNotary] = useState(false);

    useEffect(() => {
      apiGet<{ tenant_profession?: string }>("/auth/me")
        .then((m) => setIsNotary(m.tenant_profession === "notary"))
        .catch(() => {});
      // 404 when IMAP ingestion is not configured — then simply hide the row
      apiGet<{ address: string }>(`/matters/${matter.id}/email-address`)
        .then((r) => setInboundEmail(r.address))
        .catch(() => {});
      apiGet<TeamMember[]>("/team").then(setTeam).catch(() => {});
      apiGet<{ restricted: boolean; members: { user_id: string }[] }>(
        `/matters/${matter.id}/members`
      )
        .then((r) => {
          setRestricted(r.restricted);
          setMemberIds(new Set(r.members.map((m) => m.user_id)));
        })
        .catch(() => {});
    }, [matter.id]);

    async function setResponsible(userId: string) {
      const updated = await apiPatch<Matter>(`/matters/${matter.id}`, {
        responsible_user_id: userId,
      });
      onChanged(updated);
    }

    async function saveAccess(nextRestricted: boolean, nextIds: Set<string>) {
      setRestricted(nextRestricted);
      setMemberIds(nextIds);
      try {
        await apiPut(`/matters/${matter.id}/members`, {
          restricted: nextRestricted,
          user_ids: [...nextIds],
        });
        setAccessSaved(true);
        setTimeout(() => setAccessSaved(false), 2000);
      } catch {
        /* p.sh. pa të drejta — rikthe gjendjen nga serveri */
        apiGet<{ restricted: boolean; members: { user_id: string }[] }>(
          `/matters/${matter.id}/members`
        )
          .then((r) => {
            setRestricted(r.restricted);
            setMemberIds(new Set(r.members.map((m) => m.user_id)));
          })
          .catch(() => {});
      }
    }

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
        {inboundEmail && (
          <div className="flex text-sm items-center">
            <span className="w-48 text-slate-500 shrink-0">{t.matterEmailLabel}</span>
            <span className="flex items-center gap-2 flex-wrap">
              <code className="text-xs bg-slate-100 rounded px-1.5 py-0.5">{inboundEmail}</code>
              <button
                type="button"
                className="text-xs text-indigo-600 hover:underline"
                onClick={() => {
                  navigator.clipboard.writeText(inboundEmail);
                  setEmailCopied(true);
                  setTimeout(() => setEmailCopied(false), 1500);
                }}
              >
                {emailCopied ? t.copied : t.copyLink}
              </button>
              <span className="text-xs text-slate-400">{t.matterEmailHint}</span>
            </span>
          </div>
        )}
        <div className="flex text-sm items-center">
          <span className="w-48 text-slate-500 shrink-0">
            {isNotary ? t.responsiblePerson : t.responsibleLawyer}
          </span>
          {team.length > 1 ? (
            <Select
              value={matter.responsible_user_id || ""}
              onChange={(e) => setResponsible(e.target.value)}
              className="max-w-64"
            >
              {team.filter((m) => m.is_active).map((m) => (
                <option key={m.id} value={m.id}>{m.full_name}</option>
              ))}
            </Select>
          ) : (
            <span>{team[0]?.full_name || "—"}</span>
          )}
        </div>
        {team.length > 1 && (
          <div className="pt-3 border-t border-slate-100 space-y-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={restricted}
                onChange={(e) => saveAccess(e.target.checked, memberIds)}
              />
              <span className="font-medium">{t.restrictedMatter}</span>
              {accessSaved && <span className="text-emerald-600 text-xs">✓ {t.saved}</span>}
            </label>
            <p className="text-xs text-slate-500">{t.restrictedHint}</p>
            {restricted && (
              <div className="flex flex-wrap gap-3 pt-1">
                {team
                  .filter((m) => m.is_active && m.id !== matter.responsible_user_id)
                  .map((m) => (
                    <label key={m.id} className="flex items-center gap-1.5 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={memberIds.has(m.id)}
                        onChange={(e) => {
                          const next = new Set(memberIds);
                          if (e.target.checked) next.add(m.id);
                          else next.delete(m.id);
                          saveAccess(true, next);
                        }}
                      />
                      {m.full_name}
                    </label>
                  ))}
              </div>
            )}
          </div>
        )}
        {matter.description && (
          <div className="pt-3 border-t border-slate-100 text-sm whitespace-pre-wrap">
            {matter.description}
          </div>
        )}
      </Card>
    );
  }
}

interface DeckungInfo {
  insurer_code: string | null;
  insurance_status: string | null;
  insurance_requested_at: string | null;
  followup_due: boolean;
  followup_days: number;
  insurers: { code: string; name: string; email: string; website: string }[];
}

/** Rechtsschutz cover tracking (DE matters, D-045): one-click Deckungsanfrage
 * into the documents + insurer answer tracking. Hidden for non-DE matters
 * (the endpoint 404s there). */
function DeckungCard({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [info, setInfo] = useState<DeckungInfo | null>(null);
  const [insurerCode, setInsurerCode] = useState("");
  const [policy, setPolicy] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    apiGet<DeckungInfo>(`/matters/${matterId}/deckung`).then(setInfo).catch(() => {});
  }, [matterId]);

  useEffect(load, [load]);

  if (!info) return null;

  async function createAnfrage() {
    if (!insurerCode) return;
    setBusy(true);
    setError("");
    setCreated(false);
    try {
      await apiPost(`/matters/${matterId}/deckung/anfrage`, {
        insurer_code: insurerCode,
        policy_number: policy,
      });
      setCreated(true);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(status: string | null) {
    setError("");
    try {
      await apiPost(`/matters/${matterId}/deckung/status`, { status });
      setCreated(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  const statusLabel: Record<string, string> = {
    angefragt: t.dkgStatusAngefragt,
    bestaetigt: t.dkgStatusBestaetigt,
    abgelehnt: t.dkgStatusAbgelehnt,
  };
  const statusColor: Record<string, string> = {
    angefragt: "bg-amber-50 text-amber-700 border-amber-200",
    bestaetigt: "bg-emerald-50 text-emerald-700 border-emerald-200",
    abgelehnt: "bg-red-50 text-red-700 border-red-200",
  };
  const insurerName =
    info.insurers.find((i) => i.code === info.insurer_code)?.name || info.insurer_code;

  return (
    <Card className="p-5 mt-4 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <h3 className="font-semibold text-sm">🛡️ {t.dkgTitle}</h3>
        {info.insurance_status && (
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusColor[info.insurance_status]}`}
          >
            {statusLabel[info.insurance_status]} · {insurerName}
          </span>
        )}
      </div>
      <ErrorNote message={error} />
      {created && <p className="text-sm text-emerald-700">✓ {t.dkgCreated}</p>}

      {!info.insurance_status ? (
        <>
          <p className="text-xs text-slate-500">{t.dkgHint}</p>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <Label>{t.dkgInsurer}</Label>
              <Select
                value={insurerCode}
                onChange={(e) => setInsurerCode(e.target.value)}
                className="min-w-56"
              >
                <option value="">—</option>
                {info.insurers.map((i) => (
                  <option key={i.code} value={i.code}>{i.name}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t.dkgPolicy}</Label>
              <Input value={policy} onChange={(e) => setPolicy(e.target.value)} />
            </div>
            <Button onClick={createAnfrage} disabled={!insurerCode || busy}>
              {busy ? t.loading : t.dkgCreate}
            </Button>
          </div>
        </>
      ) : (
        <div className="space-y-2">
          {info.insurance_requested_at && (
            <p className="text-xs text-slate-500">
              {t.dkgRequestedOn.replace(
                "{date}",
                new Date(info.insurance_requested_at).toLocaleDateString()
              )}
            </p>
          )}
          {info.followup_due && info.insurance_status === "angefragt" && (
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              ⏰ {t.dkgFollowup.replace("{n}", String(info.followup_days))}
            </p>
          )}
          <div className="flex gap-3 text-xs">
            {info.insurance_status === "angefragt" && (
              <>
                <button
                  onClick={() => setStatus("bestaetigt")}
                  className="text-emerald-700 hover:underline"
                >
                  {t.dkgMarkConfirmed}
                </button>
                <button
                  onClick={() => setStatus("abgelehnt")}
                  className="text-red-600 hover:underline"
                >
                  {t.dkgMarkDeclined}
                </button>
              </>
            )}
            <button onClick={() => setStatus(null)} className="text-slate-500 hover:underline">
              {t.dkgReset}
            </button>
          </div>
        </div>
      )}
    </Card>
  );
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

function Documents({ matterId, clientId }: { matterId: string; clientId: string | null }) {
  const { t } = useI18n();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sigs, setSigs] = useState<SigRequest[]>([]);
  const [extractingId, setExtractingId] = useState<string | null>(null);
  const [proposals, setProposals] = useState<ExtractedDeadline[] | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [notice, setNotice] = useState("");
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [me, setMe] = useState<{ id: string; role: string } | null>(null);
  const [previewDoc, setPreviewDoc] = useState<{ doc: Doc; url: string } | null>(null);
  const [summarizingId, setSummarizingId] = useState<string | null>(null);
  const [aiSummary, setAiSummary] = useState<{ doc: Doc; data: DocAiSummary } | null>(null);

  const load = useCallback(() => {
    apiGet<Doc[]>(`/matters/${matterId}/documents`).then(setDocs).catch(() => {});
    apiGet<SigRequest[]>(`/matters/${matterId}/signatures`).then(setSigs).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    apiGet<TeamMember[]>("/team").then(setTeam).catch(() => {});
    apiGet<{ id: string; role: string }>("/auth/me").then(setMe).catch(() => {});
  }, [load]);

  async function sendForReview(doc: Doc, reviewerId: string) {
    if (!reviewerId) return;
    setError("");
    try {
      await apiPost(`/documents/${doc.id}/request-review`, { reviewer_id: reviewerId });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function decide(doc: Doc, decision: "approve" | "request_changes") {
    setError("");
    let note: string | null = null;
    if (decision === "request_changes") {
      note = window.prompt(t.reviewNotePrompt) || null;
    }
    try {
      await apiPost(`/documents/${doc.id}/review`, { decision, note });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function confirmAiReview(doc: Doc) {
    setError("");
    try {
      await apiPost(`/documents/${doc.id}/confirm-ai-review`, {});
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  function aiStamp(d: Doc) {
    if (!d.ai_generated) return null;
    if (d.ai_reviewed_at) {
      return (
        <span
          className="ml-2 inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
          title={t.aigReviewedOn.replace("{date}", new Date(d.ai_reviewed_at).toLocaleDateString())}
        >
          {t.aigBadge} ✓
        </span>
      );
    }
    return (
      <span
        className="ml-2 inline-flex items-center gap-1.5 px-1.5 py-0.5 rounded text-[10px] font-medium bg-violet-50 text-violet-700 border border-violet-200"
        title={t.aigNeedsReview}
      >
        {t.aigBadge}
        <button onClick={() => confirmAiReview(d)} className="underline hover:no-underline">
          {t.aigConfirm}
        </button>
      </span>
    );
  }

  function reviewCell(d: Doc) {
    const reviewerName = team.find((m) => m.id === d.reviewer_id)?.full_name || "";
    if (d.approval_status === "approved")
      return <span className="text-emerald-700">✓ {t.approvedLabel}</span>;
    if (d.approval_status === "in_review") {
      const canDecide = me && (me.id === d.reviewer_id || me.role === "admin");
      return (
        <span className="space-x-2">
          <span className="text-amber-600">{t.inReviewLabel}{reviewerName ? ` · ${reviewerName}` : ""}</span>
          {canDecide && (
            <>
              <button onClick={() => decide(d, "approve")} className="text-emerald-600 hover:underline">
                {t.approve}
              </button>
              <button onClick={() => decide(d, "request_changes")} className="text-red-600 hover:underline">
                {t.requestChanges}
              </button>
            </>
          )}
        </span>
      );
    }
    const label =
      d.approval_status === "changes_requested" ? (
        <span className="text-red-600 block" title={d.approval_note || ""}>
          {t.changesRequestedLabel}
        </span>
      ) : null;
    if (team.filter((m) => m.is_active).length < 2) return label || <span>—</span>;
    return (
      <span>
        {label}
        <select
          defaultValue=""
          onChange={(e) => sendForReview(d, e.target.value)}
          className="text-xs border border-slate-200 rounded px-1 py-0.5 text-indigo-600 max-w-36"
        >
          <option value="">{t.sendForReview}</option>
          {team
            .filter((m) => m.is_active && m.id !== me?.id)
            .map((m) => (
              <option key={m.id} value={m.id}>{m.full_name}</option>
            ))}
        </select>
      </span>
    );
  }

  async function extract(doc: Doc) {
    setExtractingId(doc.id);
    setProposals(null);
    setNotice("");
    setError("");
    try {
      const result = await apiPost<ExtractedDeadline[]>(
        `/matters/${matterId}/documents/${doc.id}/extract-deadlines`
      );
      setProposals(result);
      setSelected(new Set(result.map((p, i) => (p.due_date ? i : -1)).filter((i) => i >= 0)));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setExtractingId(null);
    }
  }

  async function acceptProposals() {
    if (!proposals) return;
    const chosen = proposals.filter((_, i) => selected.has(i));
    await apiPost(`/matters/${matterId}/deadlines/bulk`, { deadlines: chosen });
    setProposals(null);
    setNotice(t.deadlinesAdded);
  }

  async function summarize(doc: Doc) {
    setSummarizingId(doc.id);
    setError("");
    try {
      const data = await apiPost<DocAiSummary>(`/documents/${doc.id}/summarize`);
      setAiSummary({ doc, data });
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setSummarizingId(null);
    }
  }

  async function requestSignature(doc: Doc) {
    if (!clientId) return;
    setError("");
    try {
      await apiPost(`/matters/${matterId}/signatures`, {
        document_id: doc.id,
        contact_id: clientId,
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  function sigFor(docId: string): SigRequest | undefined {
    return sigs.find((s) => s.document_id === docId);
  }

  async function downloadCertificate(sig: SigRequest) {
    const res = await fetch(`/api/matters/${matterId}/signatures/${sig.id}/certificate`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `certifikata-${sig.id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const confidenceLabel: Record<string, string> = {
    high: t.confidenceHigh,
    medium: t.confidenceMedium,
    low: t.confidenceLow,
  };

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

  const canPreview = (d: Doc) =>
    d.mime_type === "application/pdf" || d.mime_type.startsWith("image/");

  async function preview(doc: Doc) {
    const res = await fetch(`/api/documents/${doc.id}/preview`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    setPreviewDoc({ doc, url: URL.createObjectURL(blob) });
  }

  function closePreview() {
    if (previewDoc) URL.revokeObjectURL(previewDoc.url);
    setPreviewDoc(null);
  }

  async function toggleVisibility(doc: Doc) {
    setError("");
    try {
      await apiPost(`/documents/${doc.id}/visibility`, {
        visible: !doc.visible_to_client,
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
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
        {notice && <span className="text-sm text-emerald-700">✓ {notice}</span>}
      </div>

      {extractingId && (
        <p className="text-sm text-slate-500 animate-pulse">{t.extracting}</p>
      )}

      {proposals !== null && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold text-sm">{t.proposedDeadlines}</h3>
          {proposals.length === 0 ? (
            <p className="text-sm text-slate-500">{t.noProposals}</p>
          ) : (
            <>
              <div className="divide-y divide-slate-100">
                {proposals.map((p, i) => (
                  <label key={i} className="flex items-start gap-3 py-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      className="mt-1"
                      disabled={!p.due_date}
                      checked={selected.has(i)}
                      onChange={(e) => {
                        const next = new Set(selected);
                        if (e.target.checked) next.add(i);
                        else next.delete(i);
                        setSelected(next);
                      }}
                    />
                    <div>
                      <p className="font-medium">
                        {p.title}{" "}
                        <span className="text-xs font-normal text-slate-400">
                          ({t.confidence}: {confidenceLabel[p.confidence] || p.confidence})
                        </span>
                      </p>
                      <p className="text-xs text-slate-500">
                        {p.due_date
                          ? new Date(p.due_date).toLocaleDateString()
                          : `${p.days ? `${p.days} ${t.agingDays}` : ""} — ${t.needsDate}`}
                        {p.legal_basis && ` · ${p.legal_basis}`}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
              <div className="flex gap-2">
                <Button onClick={acceptProposals} disabled={selected.size === 0}>
                  {t.acceptSelected} ({selected.size})
                </Button>
                <Button variant="secondary" onClick={() => setProposals(null)}>
                  {t.cancel}
                </Button>
              </div>
            </>
          )}
        </Card>
      )}

      <Card>
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[760px]">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
              <th className="px-4 py-3">{t.name}</th>
              <th className="px-4 py-3">{t.version}</th>
              <th className="px-4 py-3">OCR</th>
              <th className="px-4 py-3">{t.reviewLabel}</th>
              <th className="px-4 py-3">{t.signatures}</th>
              <th className="px-4 py-3" title={t.visibleToClient}>{t.sharedWithClient}</th>
              <th className="px-4 py-3">{t.uploaded}</th>
              <th className="px-4 py-3">{t.actions}</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => {
              const sig = sigFor(d.id);
              return (
                <tr key={d.id} className="border-b border-slate-100">
                  <td className="px-4 py-3">
                    {d.filename}
                    {aiStamp(d)}
                  </td>
                  <td className="px-4 py-3">v{d.version}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {d.has_text ? "✓" : d.ocr_status}
                  </td>
                  <td className="px-4 py-3 text-xs">{reviewCell(d)}</td>
                  <td className="px-4 py-3 text-xs">
                    {sig ? (
                      sig.status === "signed" ? (
                        <span className="text-emerald-700">
                          ✓ {t.signedByOn} {sig.signer_name}{" "}
                          <button
                            onClick={() => downloadCertificate(sig)}
                            className="text-indigo-600 hover:underline"
                          >
                            {t.certificate}
                          </button>
                        </span>
                      ) : sig.status === "declined" ? (
                        <span className="text-red-600">{t.declinedLabel}</span>
                      ) : (
                        <span className="text-amber-600">{t.pendingSignature}</span>
                      )
                    ) : clientId ? (
                      <button
                        onClick={() => requestSignature(d)}
                        className="text-indigo-600 hover:underline"
                      >
                        {t.requestSignature}
                      </button>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      className="cursor-pointer"
                      title={t.visibleToClient}
                      checked={d.visible_to_client}
                      onChange={() => toggleVisibility(d)}
                    />
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(d.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 space-x-3 whitespace-nowrap">
                    {canPreview(d) && (
                      <button onClick={() => preview(d)} className="text-indigo-600 hover:underline text-xs">
                        {t.previewLabel}
                      </button>
                    )}
                    <button onClick={() => download(d)} className="text-indigo-600 hover:underline text-xs">
                      {t.download}
                    </button>
                    {d.has_text && (
                      <button
                        onClick={() => extract(d)}
                        disabled={extractingId !== null}
                        className="text-violet-600 hover:underline text-xs disabled:text-slate-300"
                      >
                        {t.extractDeadlines}
                      </button>
                    )}
                    {d.has_text && (
                      <button
                        onClick={() => summarize(d)}
                        disabled={summarizingId !== null}
                        className="text-violet-600 hover:underline text-xs disabled:text-slate-300"
                      >
                        {summarizingId === d.id ? t.loading : t.docSummarize}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </Card>

      {aiSummary && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
          onClick={() => setAiSummary(null)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200 sticky top-0 bg-white">
              <p className="text-sm font-semibold truncate">
                ✦ {t.docSummaryTitle} — {aiSummary.doc.filename}
              </p>
              <button
                onClick={() => setAiSummary(null)}
                className="text-slate-400 hover:text-slate-700 text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <div className="p-5 space-y-4 text-sm">
              <p className="leading-relaxed whitespace-pre-wrap">{aiSummary.data.summary}</p>
              {aiSummary.data.key_points.length > 0 && (
                <div>
                  <p className="font-semibold text-slate-700 mb-1">{t.docKeyPoints}</p>
                  <ul className="space-y-1 text-slate-600">
                    {aiSummary.data.key_points.map((p, i) => (
                      <li key={i}>• {p}</li>
                    ))}
                  </ul>
                </div>
              )}
              {aiSummary.data.deadlines.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
                  <p className="font-semibold text-amber-800 mb-1">⚠ {t.docPossibleDeadlines}</p>
                  <ul className="space-y-1 text-amber-700 text-xs">
                    {aiSummary.data.deadlines.map((p, i) => (
                      <li key={i}>
                        • {p.title}
                        {p.date ? ` — ${p.date}` : p.days ? ` — ${p.days} ${t.agingDays}` : ""}
                        {p.legal_basis ? ` (${p.legal_basis})` : ""}
                      </li>
                    ))}
                  </ul>
                  <p className="text-xs text-amber-600 mt-2">{t.docDeadlinesHint}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {previewDoc && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
          onClick={closePreview}
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-200">
              <p className="text-sm font-medium truncate">{previewDoc.doc.filename}</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => download(previewDoc.doc)}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  {t.download}
                </button>
                <button onClick={closePreview} className="text-slate-400 hover:text-slate-700 text-lg leading-none">
                  ✕
                </button>
              </div>
            </div>
            {previewDoc.doc.mime_type.startsWith("image/") ? (
              <div className="flex-1 overflow-auto flex items-center justify-center bg-slate-50">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={previewDoc.url} alt={previewDoc.doc.filename} className="max-w-full max-h-full" />
              </div>
            ) : (
              <iframe src={previewDoc.url} className="flex-1 w-full" title={previewDoc.doc.filename} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Tasks({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [form, setForm] = useState({ title: "", due_date: "", priority: "normal", assignee_id: "" });
  const [error, setError] = useState("");

  const priorityLabel: Record<string, string> = {
    low: t.priorityLow, normal: t.priorityNormal, high: t.priorityHigh, urgent: t.priorityUrgent,
  };
  const statusLabel: Record<string, string> = {
    open: t.taskOpen, in_progress: t.taskInProgress, done: t.taskDone, cancelled: t.taskCancelled,
  };

  const load = useCallback(() => {
    apiGet<Task[]>(`/tasks?matter_id=${matterId}`).then(setTasks).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    apiGet<TeamMember[]>("/team").then(setTeam).catch(() => {});
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/tasks", {
        matter_id: matterId,
        title: form.title,
        due_date: form.due_date || null,
        priority: form.priority,
        assignee_id: form.assignee_id || null,
      });
      setForm({ ...form, title: "", due_date: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function setStatus(task: Task, status: string) {
    await apiPatch(`/tasks/${task.id}`, { status });
    load();
  }

  async function remove(task: Task) {
    await apiDelete(`/tasks/${task.id}`);
    load();
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <form onSubmit={add} className="flex gap-3 items-end flex-wrap">
          <div className="flex-[2] min-w-56">
            <Label>{t.title}</Label>
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </div>
          <div>
            <Label>{t.dueDate}</Label>
            <Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          </div>
          <div className="w-32">
            <Label>{t.priority}</Label>
            <Select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              {(["low", "normal", "high", "urgent"] as const).map((p) => (
                <option key={p} value={p}>{priorityLabel[p]}</option>
              ))}
            </Select>
          </div>
          {team.filter((m) => m.is_active).length > 1 && (
            <div className="w-44">
              <Label>{t.assignee}</Label>
              <Select value={form.assignee_id} onChange={(e) => setForm({ ...form, assignee_id: e.target.value })}>
                <option value="">—</option>
                {team.filter((m) => m.is_active).map((m) => (
                  <option key={m.id} value={m.id}>{m.full_name}</option>
                ))}
              </Select>
            </div>
          )}
          <Button type="submit">{t.addTask}</Button>
        </form>
        <div className="mt-2"><ErrorNote message={error} /></div>
      </Card>

      <Card>
        {tasks.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-6">{t.noTasks}</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {tasks.map((task) => {
              const overdue =
                task.due_date && task.status !== "done" && new Date(task.due_date) < new Date();
              const assigneeName = team.find((m) => m.id === task.assignee_id)?.full_name;
              return (
                <div key={task.id} className="flex items-center gap-3 px-4 py-3 text-sm">
                  <input
                    type="checkbox"
                    className="cursor-pointer"
                    checked={task.status === "done"}
                    onChange={() => setStatus(task, task.status === "done" ? "open" : "done")}
                  />
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium ${task.status === "done" ? "line-through text-slate-400" : ""}`}>
                      {task.title}
                    </p>
                    <p className="text-xs text-slate-500">
                      {task.due_date && (
                        <span className={overdue ? "text-red-600 font-semibold" : ""}>
                          {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                      {task.due_date && assigneeName && " · "}
                      {assigneeName}
                    </p>
                  </div>
                  {(task.priority === "high" || task.priority === "urgent") && task.status !== "done" && (
                    <Badge status="overdue" label={priorityLabel[task.priority]} />
                  )}
                  <Badge status={task.status === "done" ? "paid" : "open"} label={statusLabel[task.status] || task.status} />
                  <button onClick={() => remove(task)} className="text-xs text-red-400 hover:text-red-600">✕</button>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}

function Messages({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<MatterMsg[]>([]);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    apiGet<MatterMsg[]>(`/matters/${matterId}/messages`).then(setMessages).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, [load]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    try {
      await apiPost(`/matters/${matterId}/messages`, { body });
      setBody("");
      load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="p-4 space-y-3 max-h-[28rem] overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-6">{t.noMessages}</p>
        )}
        {messages.map((m) => {
          const fromClient = m.sender_contact_id !== null;
          return (
            <div key={m.id} className={`flex ${fromClient ? "justify-start" : "justify-end"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
                  fromClient
                    ? "bg-slate-100 text-slate-800"
                    : "bg-indigo-600 text-white"
                }`}
              >
                <p className="whitespace-pre-wrap">{m.body}</p>
                <p className={`text-[10px] mt-1 ${fromClient ? "text-slate-400" : "text-indigo-200"}`}>
                  {fromClient ? t.clientLabel : t.youLabel} · {new Date(m.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          );
        })}
      </Card>
      <form onSubmit={send} className="flex gap-2">
        <Input
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder={t.writeMessage}
          className="flex-1"
        />
        <Button type="submit" disabled={busy || !body.trim()}>{t.send}</Button>
      </form>
    </div>
  );
}

type DlSuggestion = {
  id: string;
  kind: string;
  title: string;
  due_date: string | null;
  rule_id: string | null;
  trigger_date: string | null;
  legal_basis: string | null;
  confidence: string;
  document_filename: string | null;
  rule_name: Record<string, string> | null;
  matter_id: string;
  matter_reference?: string | null;
  matter_title?: string | null;
};

function Deadlines({ matterId, practiceArea }: { matterId: string; practiceArea: string }) {
  const { t, locale } = useI18n();
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [suggestions, setSuggestions] = useState<DlSuggestion[]>([]);
  const [sugDates, setSugDates] = useState<Record<string, string>>({});
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
    apiGet<DlSuggestion[]>(`/matters/${matterId}/deadline-suggestions`)
      .then(setSuggestions)
      .catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    // rules of the matter's own jurisdiction (multi-country, D-034)
    apiGet<DeadlineRule[]>(`/matters/${matterId}/deadline-rules`).then(setRules).catch(() => {});
  }, [load, matterId]);

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

  async function acceptSuggestion(s: DlSuggestion) {
    setError("");
    const body: Record<string, string> = {};
    // Rule matched but no trigger date extracted → the lawyer supplies it
    if (s.rule_id && !s.trigger_date && !s.due_date) {
      const picked = sugDates[s.id];
      if (!picked) return;
      body.trigger_date = picked;
    }
    try {
      await apiPost(`/deadline-suggestions/${s.id}/accept`, body);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function dismissSuggestion(id: string) {
    try {
      await apiPost(`/deadline-suggestions/${id}/dismiss`);
      load();
    } catch {}
  }

  return (
    <div className="space-y-4">
      {suggestions.length > 0 && (
        <Card className="p-4 border-indigo-200 bg-indigo-50/50">
          <p className="font-semibold text-sm text-indigo-900">{t.dlsTitle}</p>
          <p className="text-xs text-indigo-700 mb-2">{t.dlsHint}</p>
          <div className="divide-y divide-indigo-100">
            {suggestions.map((s) => (
              <div key={s.id} className="py-2 flex flex-wrap items-center gap-2 text-sm">
                <div className="flex-1 min-w-48">
                  <p className="font-medium">{s.title}</p>
                  <p className="text-xs text-slate-500">
                    {[
                      s.legal_basis,
                      s.due_date || s.trigger_date
                        ? new Date(s.due_date || s.trigger_date!).toLocaleDateString()
                        : null,
                      s.document_filename,
                      `${t.confidence}: ${
                        (t as Record<string, string>)[
                          `confidence${s.confidence.charAt(0).toUpperCase()}${s.confidence.slice(1)}`
                        ] || s.confidence
                      }`,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
                {s.rule_id && !s.trigger_date && !s.due_date && (
                  <Input
                    type="date"
                    className="w-40"
                    title={t.triggerDate}
                    value={sugDates[s.id] || ""}
                    onChange={(e) =>
                      setSugDates((prev) => ({ ...prev, [s.id]: e.target.value }))
                    }
                  />
                )}
                <button
                  onClick={() => acceptSuggestion(s)}
                  className="text-xs font-medium text-emerald-700 hover:underline"
                >
                  {t.tsAccept}
                </button>
                <button
                  onClick={() => dismissSuggestion(s.id)}
                  className="text-xs text-slate-500 hover:underline"
                >
                  {t.tsDismiss}
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}
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
                      {localized(r.name, locale)} ({r.days}{" "}
                      {r.day_type === "months" ? t.dcMonthsShort : t.dcDaysShort} —{" "}
                      {r.legal_basis})
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
  const { t, locale } = useI18n();
  const [notes, setNotes] = useState<Note[]>([]);
  const [body, setBody] = useState("");
  const voice = useVoiceAvailable();

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
          <div className="flex items-center gap-2">
            <Button type="submit">{t.addNote}</Button>
            {voice.stt && (
              <MicButton
                locale={locale}
                onText={(text) => setBody((prev) => (prev ? `${prev} ${text}` : text))}
              />
            )}
          </div>
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

const DRAFT_MARKER = "=== DRAFT-SHKRESA ===";

interface OvCheck {
  code: string;
  ok: boolean | null;
  court?: { name: string; state: string; scope: string; live_from: string };
}

interface OvResult {
  eligible: boolean;
  is_flight_case: boolean;
  suggested_template: string;
  template_id: string | null;
  checks: OvCheck[];
  matched_court: { name: string } | null;
  portal_url: string;
  fees: { regular_advance: string; ov_advance: string; saving: string } | null;
}

function MatterAI({ matterId }: { matterId: string }) {
  const { t, locale } = useI18n();
  const [output, setOutput] = useState("");
  const [isDraft, setIsDraft] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sentToPortal, setSentToPortal] = useState(false);
  const [copiedText, setCopiedText] = useState(false);
  const [prepStep, setPrepStep] = useState("");
  const [copiedDraft, setCopiedDraft] = useState(false);
  // Zivilgerichtliches Online-Verfahren (DE matters, D-041)
  const [ovOpen, setOvOpen] = useState(false);
  const [ovValue, setOvValue] = useState("");
  const [ov, setOv] = useState<OvResult | null>(null);
  const [ovBusy, setOvBusy] = useState(false);
  const [ovAvailable, setOvAvailable] = useState(false);

  useEffect(() => {
    // The endpoint 404s for non-DE matters — probe once to decide visibility
    apiGet<OvResult>(`/matters/${matterId}/online-verfahren`)
      .then(() => setOvAvailable(true))
      .catch(() => setOvAvailable(false));
  }, [matterId]);

  async function checkOv() {
    setOvBusy(true);
    setError("");
    try {
      const query = ovValue ? `?value_eur=${encodeURIComponent(ovValue)}` : "";
      setOv(await apiGet<OvResult>(`/matters/${matterId}/online-verfahren${query}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setOvBusy(false);
    }
  }

  const OV_CHECK_LABELS: Record<string, string> = {
    value_ok: t.ovcValueOk,
    value_too_high: t.ovcValueHigh,
    value_unknown: t.ovcValueUnknown,
    court_pilot: t.ovcCourtPilot,
    court_flight_only: t.ovcCourtFlightOnly,
    court_unknown: t.ovcCourtUnknown,
    payment_claim_manual: t.ovcPaymentManual,
  };

  /** Agentic preparation: Ava reads the file, researches each legal question
   * in the corpus and streams back analysis + next steps + a draft document. */
  async function prepare() {
    setBusy(true);
    setError("");
    setOutput("");
    setIsDraft(false);
    setPrepStep(t.prepReading);
    try {
      await apiStream(
        `/assistant/matters/${matterId}/prepare?locale=${locale}`,
        {},
        (event) => {
          if (event.type === "step") {
            if (event.step === "subquestions") setPrepStep(t.prepQuestions);
            if (event.step === "search")
              setPrepStep(`${t.prepSearching} ${event.index}/${event.total}`);
            if (event.step === "synthesis") setPrepStep(t.prepWriting);
          } else if (event.type === "delta") {
            setOutput((prev) => prev + (event.text as string));
          } else if (event.type === "error") {
            setError(String(event.detail || t.error));
          }
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
      setPrepStep("");
    }
  }

  async function run(action: "summarize" | "hearing" | "clientUpdate") {
    setBusy(true);
    setError("");
    setOutput("");
    setIsDraft(action === "clientUpdate");
    setSentToPortal(false);
    try {
      if (action === "clientUpdate") {
        const result = await apiPost<{ draft: string }>(
          `/matters/${matterId}/client-update-draft`, {}
        );
        setOutput(result.draft);
      } else {
        const result =
          action === "summarize"
            ? await apiPost<{ summary: string }>(`/assistant/matters/${matterId}/summarize`)
            : await apiPost<{ summary: string }>(`/assistant/hearing-prep`, { matter_id: matterId });
        setOutput(result.summary);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function sendDraftToPortal() {
    await apiPost(`/matters/${matterId}/messages`, { body: output });
    setSentToPortal(true);
  }

  async function copyDraft() {
    await navigator.clipboard.writeText(output);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        <Button onClick={prepare} disabled={busy}>✦ {t.prepMatter}</Button>
        <Button onClick={() => run("summarize")} disabled={busy} variant="secondary">{t.summarizeMatter}</Button>
        <Button onClick={() => run("hearing")} disabled={busy} variant="secondary">{t.hearingPrep}</Button>
        <Button onClick={() => run("clientUpdate")} disabled={busy} variant="secondary">
          {t.draftClientUpdate}
        </Button>
        {ovAvailable && (
          <Button onClick={() => setOvOpen((v) => !v)} disabled={busy} variant="secondary">
            ⚖ {t.ovCheckBtn}
          </Button>
        )}
      </div>
      <ErrorNote message={error} />
      {ovOpen && (
        <Card className="p-5 space-y-3">
          <h3 className="text-sm font-semibold">{t.ovTitle}</h3>
          <div className="flex gap-2 items-end flex-wrap">
            <div>
              <Label>{t.rvgValue}</Label>
              <Input
                type="number"
                min="1"
                value={ovValue}
                onChange={(e) => setOvValue(e.target.value)}
                className="w-40"
              />
            </div>
            <Button onClick={checkOv} disabled={ovBusy}>
              {ovBusy ? t.loading : t.ovCheckBtn}
            </Button>
          </div>
          {ov && (
            <div className="space-y-3">
              <p
                className={`text-sm font-semibold ${
                  ov.eligible ? "text-emerald-700" : "text-amber-700"
                }`}
              >
                {ov.eligible ? t.ovEligible : t.ovNotEligible}
              </p>
              <ul className="space-y-1">
                {ov.checks.map((check) => (
                  <li key={check.code} className="flex items-start gap-2 text-sm text-slate-600">
                    <span>
                      {check.ok === true ? "✓" : check.ok === false ? "✗" : "•"}
                    </span>
                    <span>
                      {OV_CHECK_LABELS[check.code] || check.code}
                      {check.court ? ` — ${check.court.name}` : ""}
                    </span>
                  </li>
                ))}
              </ul>
              {ov.fees && (
                <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-sm text-slate-700 space-y-0.5">
                  <div className="flex justify-between">
                    <span>{t.ovFeeRegular}</span>
                    <span className="font-mono">{Number(ov.fees.regular_advance).toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between">
                    <span>{t.ovFeeOv}</span>
                    <span className="font-mono">{Number(ov.fees.ov_advance).toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between font-semibold text-emerald-700">
                    <span>{t.ovFeeSaving}</span>
                    <span className="font-mono">−{Number(ov.fees.saving).toFixed(2)} €</span>
                  </div>
                </div>
              )}
              <div className="flex gap-2 flex-wrap">
                {ov.template_id && (
                  <Button
                    variant="secondary"
                    onClick={() =>
                      apiDownload("/templates/render-docx", "ov-klageschrift.docx", {
                        method: "POST",
                        body: {
                          template_id: ov.template_id,
                          matter_id: matterId,
                          variables: ovValue ? { claim_amount: ovValue, claim_value: ovValue, compensation: ovValue } : {},
                        },
                      })
                    }
                  >
                    {t.ovOpenTemplate}
                  </Button>
                )}
                <Button
                  variant="secondary"
                  onClick={() =>
                    apiDownload(
                      `/matters/${matterId}/ov-export${ovValue ? `?value_eur=${encodeURIComponent(ovValue)}` : ""}`,
                      "ov-export.json"
                    )
                  }
                >
                  {t.ovExportJson}
                </Button>
              </div>
              <p className="text-xs text-slate-400">{t.ovSubmitHint}</p>
            </div>
          )}
        </Card>
      )}
      {busy && (
        <p className="text-sm text-slate-500 animate-pulse">{prepStep || t.thinking}</p>
      )}
      {output && (
        <Card className="p-5 space-y-4">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">
            {output.split(DRAFT_MARKER)[0].trim()}
          </p>
          {output.includes(DRAFT_MARKER) && (
            <div className="pt-3 border-t border-slate-100 space-y-3">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <h3 className="text-sm font-semibold text-indigo-700">{t.prepDraftTitle}</h3>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={() =>
                      apiDownload("/assistant/export-docx", "draft.docx", {
                        method: "POST",
                        body: {
                          content: output.split(DRAFT_MARKER)[1].trim(),
                          title: t.prepDraftTitle,
                        },
                      })
                    }
                  >
                    .docx
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={async () => {
                      await navigator.clipboard.writeText(
                        output.split(DRAFT_MARKER)[1].trim()
                      );
                      setCopiedDraft(true);
                      setTimeout(() => setCopiedDraft(false), 2000);
                    }}
                  >
                    {copiedDraft ? t.copied : t.copyText}
                  </Button>
                </div>
              </div>
              <p className="text-sm whitespace-pre-wrap leading-relaxed bg-slate-50 rounded-lg p-4 border border-slate-100">
                {output.split(DRAFT_MARKER)[1].trim()}
              </p>
            </div>
          )}
          {isDraft && (
            <div className="flex gap-2 items-center pt-3 border-t border-slate-100">
              <Button onClick={sendDraftToPortal} disabled={sentToPortal}>
                {sentToPortal ? "✓" : t.sendToPortal}
              </Button>
              <Button variant="secondary" onClick={copyDraft}>
                {copiedText ? t.copied : t.copyText}
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

// ---------- AML (Law 05/L-096): per-matter checklist + suspicion reports ----------

interface AmlIndicator {
  code: string;
  category: string;
  text: Record<string, string>;
}

interface AmlReport {
  id: string;
  matter_id: string | null;
  indicators: string[];
  description: string;
  status: string;
  submitted_at: string | null;
  created_at: string;
}

function AmlTab({ matterId, clientId }: { matterId: string; clientId: string | null }) {
  const { t, locale } = useI18n();
  const [indicators, setIndicators] = useState<AmlIndicator[]>([]);
  const [scopeHint, setScopeHint] = useState<Record<string, string>>({});
  const [inScope, setInScope] = useState(false);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [notes, setNotes] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [reports, setReports] = useState<AmlReport[]>([]);
  const [showReportForm, setShowReportForm] = useState(false);
  const [reportDesc, setReportDesc] = useState("");

  const loadReports = useCallback(() => {
    apiGet<AmlReport[]>("/aml/reports")
      .then((all) => setReports(all.filter((r) => r.matter_id === matterId)))
      .catch(() => {});
  }, [matterId]);

  useEffect(() => {
    apiGet<{ indicators: AmlIndicator[]; scope_hint: Record<string, string> }>("/aml/indicators")
      .then((r) => {
        setIndicators(r.indicators);
        setScopeHint(r.scope_hint);
      })
      .catch(() => {});
    apiGet<{ in_scope: boolean; checked: Record<string, boolean>; notes: string | null }>(
      `/aml/matters/${matterId}/checklist`
    )
      .then((r) => {
        setInScope(r.in_scope);
        setChecked(r.checked || {});
        setNotes(r.notes || "");
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
    loadReports();
  }, [matterId, loadReports]);

  async function save() {
    setError("");
    setSaved(false);
    try {
      await apiPut(`/aml/matters/${matterId}/checklist`, {
        in_scope: inScope,
        checked,
        notes: notes || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function createReport(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/aml/reports", {
        matter_id: matterId,
        contact_id: clientId,
        indicators: Object.keys(checked).filter((k) => checked[k]),
        description: reportDesc,
      });
      setReportDesc("");
      setShowReportForm(false);
      loadReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function submitReport(id: string) {
    await apiPost(`/aml/reports/${id}/submit`);
    loadReports();
  }

  if (!loaded) return <Spinner />;

  const flaggedCount = Object.values(checked).filter(Boolean).length;

  return (
    <div className="space-y-4">
      <Card className="p-5 space-y-4">
        <div>
          <h2 className="font-semibold">{t.amlChecklist}</h2>
          <p className="text-xs text-slate-500 mt-1">{scopeHint[locale] || scopeHint.sq}</p>
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={inScope}
            onChange={(e) => setInScope(e.target.checked)}
            className="accent-indigo-600"
          />
          {t.amlInScope}
        </label>
        {inScope && (
          <>
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <p className="text-sm font-medium">{t.amlIndicators}</p>
              {indicators.map((ind) => (
                <label key={ind.code} className="flex items-start gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!!checked[ind.code]}
                    onChange={(e) => setChecked({ ...checked, [ind.code]: e.target.checked })}
                    className="mt-0.5 accent-amber-600"
                  />
                  <span className={checked[ind.code] ? "text-amber-800" : "text-slate-600"}>
                    {ind.text[locale] || ind.text.sq}
                  </span>
                </label>
              ))}
            </div>
            <div>
              <Label>{t.notes}</Label>
              <Textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
          </>
        )}
        <div className="flex items-center gap-3">
          <Button onClick={save}>{t.save}</Button>
          {saved && <span className="text-sm text-emerald-600">✓ {t.saved}</span>}
          <ErrorNote message={error} />
        </div>
      </Card>

      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold">{t.suspicionReports}</h2>
            <p className="text-xs text-slate-500 mt-1">{t.amlNotifyOfficerOnly}</p>
          </div>
          <Button variant="secondary" onClick={() => setShowReportForm(!showReportForm)}>
            {t.newSuspicionReport}
          </Button>
        </div>
        {showReportForm && (
          <form onSubmit={createReport} className="space-y-3 pt-2 border-t border-slate-100">
            {flaggedCount > 0 && (
              <p className="text-xs text-slate-500">
                {t.amlIndicators}: {flaggedCount}
              </p>
            )}
            <div>
              <Label>{t.description}</Label>
              <Textarea
                rows={4}
                value={reportDesc}
                onChange={(e) => setReportDesc(e.target.value)}
                required
                minLength={10}
              />
            </div>
            <Button type="submit">{t.save}</Button>
          </form>
        )}
        {reports.length > 0 && (
          <div className="divide-y divide-slate-100">
            {reports.map((r) => (
              <div key={r.id} className="py-2.5 flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm truncate">{r.description}</p>
                  <p className="text-xs text-slate-400">
                    {new Date(r.created_at).toLocaleDateString()} ·{" "}
                    {r.status === "submitted"
                      ? `${t.submittedOn} ${r.submitted_at ? new Date(r.submitted_at).toLocaleDateString() : ""}`
                      : t.draftStatus}
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() =>
                      apiDownload(`/aml/reports/${r.id}/pdf`, `raport-dyshimi-${r.id.slice(0, 8)}.pdf`)
                    }
                    className="text-xs text-indigo-600 hover:underline"
                  >
                    PDF
                  </button>
                  {r.status !== "submitted" && (
                    <button
                      onClick={() => submitReport(r.id)}
                      className="text-xs text-emerald-600 hover:underline"
                    >
                      {t.markSubmitted}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
