"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiDownload, apiGet, apiPost, apiPut } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import BookingsPanel from "@/components/bookings-panel";
import { Button, Card, ErrorNote, Spinner, Textarea } from "@/components/ui";
import VideoCall, { CallGrant } from "@/components/video-call";

interface OpenCase {
  id: string;
  category: string;
  description: string;
  city: string | null;
  urgency: string;
  status: string;
  created_at: string;
  citizen_name: string;
  citizen_locale: string;
  directed_to_me: boolean;
  matches_profile?: boolean;
  has_legal_insurance?: boolean | null;
  insurer_name?: string | null;
}

interface MyCase extends OpenCase {
  citizen_email: string;
  citizen_phone: string | null;
  intake_request_id: string | null;
}

interface CaseMessage {
  id: string;
  sender: string;
  body: string;
  created_at: string;
}

interface LawyerProfile {
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
}

interface LeadQuota {
  plan: string;
  limit: number | null;
  used: number | null;
  remaining: number | null;
  past_due?: boolean;
}

export default function MarketplacePage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<"open" | "mine">("open");
  const [openCases, setOpenCases] = useState<OpenCase[] | null>(null);
  const [myCases, setMyCases] = useState<MyCase[] | null>(null);
  const [error, setError] = useState("");
  const [claimResult, setClaimResult] = useState<{ id: string; conflicts: boolean } | null>(null);
  const [openChat, setOpenChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<CaseMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [profile, setProfile] = useState<LawyerProfile | null>(null);
  const [quota, setQuota] = useState<LeadQuota | null>(null);
  const [callCase, setCallCase] = useState<string | null>(null);

  const load = useCallback(() => {
    apiGet<OpenCase[]>("/marketplace/cases").then(setOpenCases).catch(() => setOpenCases([]));
    apiGet<MyCase[]>("/marketplace/cases/mine").then(setMyCases).catch(() => setMyCases([]));
    apiGet<LawyerProfile>("/marketplace/profile").then(setProfile).catch(() => {});
    apiGet<LeadQuota>("/marketplace/lead-quota").then(setQuota).catch(() => {});
  }, []);

  useEffect(load, [load]);

  async function claim(caseId: string) {
    setError("");
    try {
      const res = await apiPost<{ claimed: boolean; has_conflicts: boolean }>(
        `/marketplace/cases/${caseId}/claim`
      );
      setClaimResult({ id: caseId, conflicts: res.has_conflicts });
      setTab("mine");
      load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : t.error;
      setError(msg.toLowerCase().includes("lead limit") ? t.mkLeadLimitReached : msg);
    }
  }

  async function toggleDuty() {
    if (!profile) return;
    const next = { ...profile, sos_on_duty: !profile.sos_on_duty };
    setProfile(next);
    try {
      await apiPut("/marketplace/profile", next);
    } catch {
      setProfile(profile);
    }
  }

  async function report(caseId: string) {
    setError("");
    try {
      await apiPost(`/marketplace/cases/${caseId}/report`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    }
  }

  async function toggleChat(caseId: string) {
    if (openChat === caseId) {
      setOpenChat(null);
      return;
    }
    setOpenChat(caseId);
    setMessages(await apiGet<CaseMessage[]>(`/marketplace/cases/${caseId}/messages`));
  }

  async function sendMessage(caseId: string) {
    if (!draft.trim()) return;
    await apiPost(`/marketplace/cases/${caseId}/messages`, { body: draft.trim() });
    setDraft("");
    setMessages(await apiGet<CaseMessage[]>(`/marketplace/cases/${caseId}/messages`));
  }

  const areaLabel = (code: string) => (t[code as keyof typeof t] as string) || code;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">{t.marketplace}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.mkPublicProfileHint}</p>
        </div>
        <div className="w-full order-last">
          <PageIntro k="marketplace" title={t.marketplaceIntroT} body={t.marketplaceIntro} />
        </div>
        <div className="text-right space-y-2">
          {profile && (
            <label className="flex items-center gap-2 justify-end cursor-pointer" title={t.mkSosDutyHint}>
              <span className="text-sm font-medium text-slate-700">{t.mkSosDuty}</span>
              <button
                onClick={toggleDuty}
                role="switch"
                aria-checked={profile.sos_on_duty}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  profile.sos_on_duty ? "bg-red-600" : "bg-slate-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                    profile.sos_on_duty ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </label>
          )}
          {quota && (
            <p className="text-xs text-slate-500">
              {quota.limit === null
                ? t.mkLeadUnlimited
                : t.mkLeadQuota
                    .replace("{used}", String(quota.used))
                    .replace("{limit}", String(quota.limit))}
            </p>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <Button variant={tab === "open" ? "primary" : "secondary"} onClick={() => setTab("open")}>
          {t.mkOpenCases} {openCases ? `(${openCases.length})` : ""}
        </Button>
        <Button variant={tab === "mine" ? "primary" : "secondary"} onClick={() => setTab("mine")}>
          {t.mkMyCases} {myCases ? `(${myCases.length})` : ""}
        </Button>
      </div>

      <ErrorNote message={error} />
      {profile && profile.verification_status !== "verified" && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 flex flex-wrap items-center justify-between gap-2">
          <span>
            {profile.verification_status === "pending" ? t.mkVerifPendingNote : t.mkVerifyBanner}
          </span>
          {profile.verification_status !== "pending" && (
            <Link href="/settings#public-profile" className="font-medium underline shrink-0">
              {t.mkVerifyBannerCta}
            </Link>
          )}
        </div>
      )}
      {quota?.past_due && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3">
          {t.subPastDue}{" "}
          <Link href="/settings" className="font-medium underline">
            {t.settings}
          </Link>
        </div>
      )}
      <BookingsPanel />
      {claimResult && (
        <div
          className={`rounded-lg text-sm px-4 py-3 ${
            claimResult.conflicts
              ? "bg-red-50 border border-red-200 text-red-700"
              : "bg-emerald-50 border border-emerald-200 text-emerald-700"
          }`}
        >
          {claimResult.conflicts ? t.mkConflictWarning : t.mkClaimSuccess}{" "}
          <Link href="/intake" className="font-medium underline">
            {t.mkGoToIntake}
          </Link>
        </div>
      )}

      {tab === "open" ? (
        openCases === null ? (
          <Spinner />
        ) : openCases.length === 0 ? (
          <Card className="p-8 text-center text-sm text-slate-500">{t.mkNoOpenCases}</Card>
        ) : (
          <div className="space-y-4">
            {openCases.map((c) => (
              <Card key={c.id} className="p-5 space-y-3">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs bg-indigo-50 text-indigo-700 rounded-full px-2 py-0.5">
                      {areaLabel(c.category)}
                    </span>
                    {c.city && (
                      <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                        {c.city}
                      </span>
                    )}
                    {c.urgency === "urgent" && (
                      <span className="text-xs bg-red-50 text-red-700 rounded-full px-2 py-0.5">
                        {t.mkUrgent}
                      </span>
                    )}
                    {c.urgency === "sos" && (
                      <span className="text-xs font-bold bg-red-600 text-white rounded-full px-2 py-0.5">
                        SOS
                      </span>
                    )}
                    {c.directed_to_me && (
                      <span className="text-xs bg-amber-50 text-amber-700 rounded-full px-2 py-0.5">
                        {t.mkDirectedToYou}
                      </span>
                    )}
                    {c.matches_profile && !c.directed_to_me && (
                      <span className="text-xs bg-emerald-50 text-emerald-700 rounded-full px-2 py-0.5">
                        {t.mkMatch}
                      </span>
                    )}
                    {c.has_legal_insurance && (
                      <span
                        className="text-xs bg-sky-50 text-sky-700 rounded-full px-2 py-0.5"
                        title={c.insurer_name || undefined}
                      >
                        {t.rsvBadge}
                        {c.insurer_name ? ` · ${c.insurer_name}` : ""}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-400">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">{c.description}</p>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-slate-500">
                    {t.mkCitizen}: <span className="font-medium">{c.citizen_name}</span>
                  </p>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => report(c.id)}
                      className="text-xs text-slate-400 hover:text-red-600 hover:underline"
                    >
                      {t.mkReport}
                    </button>
                    <Button onClick={() => claim(c.id)}>{t.mkClaim}</Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )
      ) : myCases === null ? (
        <Spinner />
      ) : myCases.length === 0 ? (
        <Card className="p-8 text-center text-sm text-slate-500">{t.mkNoCases}</Card>
      ) : (
        <div className="space-y-4">
          {myCases.map((c) => (
            <Card key={c.id} className="p-5 space-y-3">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs bg-indigo-50 text-indigo-700 rounded-full px-2 py-0.5">
                    {areaLabel(c.category)}
                  </span>
                  <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                    {c.status}
                  </span>
                </div>
                <span className="text-xs text-slate-400">
                  {new Date(c.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-slate-700 whitespace-pre-wrap">{c.description}</p>
              <div className="text-xs text-slate-500 space-x-3">
                <span className="font-medium text-slate-700">{c.citizen_name}</span>
                <span>{c.citizen_email}</span>
                {c.citizen_phone && <span>{c.citizen_phone}</span>}
              </div>
              <div className="flex items-center gap-4 text-sm">
                {c.status === "claimed" && (
                  <button
                    onClick={() => toggleChat(c.id)}
                    className="text-indigo-600 font-medium hover:underline"
                  >
                    {t.mkMessages}
                  </button>
                )}
                {(c.status === "claimed" || c.status === "converted") && (
                  <button
                    onClick={() => setCallCase(c.id)}
                    className="text-red-600 font-medium hover:underline"
                  >
                    {t.mkCall}
                  </button>
                )}
                <Link href="/intake" className="text-slate-500 hover:underline">
                  {t.mkGoToIntake}
                </Link>
              </div>
              <CaseEvidence caseId={c.id} />
              {openChat === c.id && (
                <div className="border-t border-slate-100 pt-3 space-y-3">
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {messages.map((m) => (
                      <div
                        key={m.id}
                        className={`text-sm rounded-lg px-3 py-2 max-w-[85%] ${
                          m.sender === "lawyer"
                            ? "bg-indigo-600 text-white ml-auto"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {m.body}
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Textarea
                      rows={1}
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      placeholder={t.mkWriteMessage}
                      className="flex-1"
                    />
                    <Button onClick={() => sendMessage(c.id)}>{t.mkSend}</Button>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {callCase && (
        <VideoCall
          fetchGrant={() => apiPost<CallGrant>(`/marketplace/cases/${callCase}/call-token`)}
          onClose={() => setCallCase(null)}
          showRecordNotice
        />
      )}
    </div>
  );
}

interface EvidenceRow {
  id: string;
  started_at: string;
  chunk_count: number;
  total_bytes: number;
  transcript: string | null;
}

/** Evidence recordings the citizen attached to this case (SOS vault). */
function CaseEvidence({ caseId }: { caseId: string }) {
  const { t } = useI18n();
  const [rows, setRows] = useState<EvidenceRow[] | null>(null);

  useEffect(() => {
    apiGet<EvidenceRow[]>(`/marketplace/cases/${caseId}/evidence`)
      .then(setRows)
      .catch(() => setRows([]));
  }, [caseId]);

  if (!rows || rows.length === 0) return null;

  return (
    <div className="border-t border-slate-100 pt-3 space-y-2">
      <p className="text-xs font-semibold text-slate-600">🔒 {t.mkEvidenceT}</p>
      {rows.map((row) => (
        <div key={row.id} className="space-y-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
            <span>{new Date(row.started_at).toLocaleString()}</span>
            <span>
              {row.chunk_count} {t.evChunksWord} · {(row.total_bytes / 1024).toFixed(0)} KB
            </span>
            <button
              onClick={() =>
                apiDownload(
                  `/marketplace/cases/${caseId}/evidence/${row.id}/audio`,
                  `deshmia-${row.id}.webm`
                )
              }
              className="text-indigo-600 font-medium hover:underline"
            >
              ⬇ {t.evAudioBtn}
            </button>
            <button
              onClick={() =>
                apiDownload(
                  `/marketplace/cases/${caseId}/evidence/${row.id}/package`,
                  `pako-deshmie-${row.id}.pdf`
                )
              }
              className="text-indigo-600 font-medium hover:underline"
            >
              ⬇ {t.evPdfBtn}
            </button>
          </div>
          {row.transcript && (
            <p className="text-xs text-slate-600 bg-slate-50 rounded p-2 line-clamp-3">
              {row.transcript}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

