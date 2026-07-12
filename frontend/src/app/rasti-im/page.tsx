"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import {
  CitizenCase,
  CitizenInfo,
  citizenGet,
  citizenPost,
  getCitizenToken,
  setCitizenToken,
} from "@/lib/citizen";
import { Button, Card, ErrorNote, Spinner, Textarea } from "@/components/ui";
import VideoCall, { CallGrant } from "@/components/video-call";
import PublicShell from "@/components/public-shell";
import CitizenAuthForm from "@/components/citizen-auth";
import PageIntro from "@/components/page-intro";
import SosPanel from "@/components/sos-panel";
import EvidenceVault from "@/components/evidence-vault";
import { IconCalendar } from "@/components/icons";

interface CaseMessage {
  id: string;
  sender: string;
  body: string;
  created_at: string;
}

function statusStyle(status: string): string {
  switch (status) {
    case "open": return "bg-amber-50 text-amber-700";
    case "claimed": return "bg-indigo-50 text-indigo-700";
    case "converted": return "bg-emerald-50 text-emerald-700";
    default: return "bg-slate-100 text-slate-600";
  }
}

/** Progress line for an active case: posted -> taken -> converted. */
function CaseTimeline({ status, labels }: { status: string; labels: string[] }) {
  const stage = status === "open" ? 0 : status === "claimed" ? 1 : 2;
  return (
    <ol className="flex items-center gap-1.5">
      {labels.map((label, i) => (
        <li key={label} className="flex items-center gap-1.5 flex-1 min-w-0">
          <span
            className={`h-2.5 w-2.5 rounded-full shrink-0 ${
              i < stage ? "bg-emerald-500" : i === stage ? "bg-indigo-600 ring-2 ring-indigo-100" : "bg-slate-200"
            }`}
          />
          <span
            className={`text-[11px] truncate ${
              i === stage ? "font-semibold text-slate-700" : "text-slate-400"
            }`}
          >
            {label}
          </span>
          {i < labels.length - 1 && <span className="flex-1 h-px bg-slate-200 min-w-1.5" />}
        </li>
      ))}
    </ol>
  );
}

function MyCaseInner() {
  const { t, locale } = useI18n();
  const params = useSearchParams();
  const verifyToken = params.get("verifiko");

  const [citizen, setCitizen] = useState<CitizenInfo | null>(null);
  const [checking, setChecking] = useState(true);
  const [verified, setVerified] = useState(false);
  const [cases, setCases] = useState<CitizenCase[] | null>(null);
  const [openCase, setOpenCase] = useState<string | null>(null);
  const [messages, setMessages] = useState<CaseMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sosOpen, setSosOpen] = useState(params.get("sos") === "1");
  const [vaultKey, setVaultKey] = useState(0);
  const [callCase, setCallCase] = useState<string | null>(null);

  useEffect(() => {
    if (verifyToken) {
      fetch("/api/public/citizen/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: verifyToken }),
      }).then((res) => setVerified(res.ok));
    }
  }, [verifyToken]);

  const loadCases = useCallback(() => {
    citizenGet<CitizenCase[]>("/citizen/cases").then(setCases).catch(() => setCases([]));
  }, []);

  useEffect(() => {
    if (!getCitizenToken()) {
      setChecking(false);
      return;
    }
    citizenGet<CitizenInfo>("/citizen/me")
      .then((me) => {
        setCitizen(me);
        loadCases();
      })
      .catch(() => setCitizenToken(null))
      .finally(() => setChecking(false));
  }, [loadCases]);

  async function toggleMessages(caseId: string) {
    if (openCase === caseId) {
      setOpenCase(null);
      return;
    }
    setOpenCase(caseId);
    setMessages(await citizenGet<CaseMessage[]>(`/citizen/cases/${caseId}/messages`));
  }

  async function sendMessage(caseId: string) {
    if (!draft.trim()) return;
    await citizenPost(`/citizen/cases/${caseId}/messages`, { body: draft.trim() });
    setDraft("");
    setMessages(await citizenGet<CaseMessage[]>(`/citizen/cases/${caseId}/messages`));
  }

  async function closeCase(caseId: string) {
    await citizenPost(`/citizen/cases/${caseId}/close`);
    loadCases();
  }

  const statusLabel: Record<string, string> = {
    open: t.mkStatusOpen,
    claimed: t.mkStatusClaimed,
    converted: t.mkStatusConverted,
    closed: t.mkStatusClosed,
  };

  return (
    <PublicShell>
      <main className="w-full max-w-2xl mx-auto px-4 py-8 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">{t.mkMyCases}</h1>
          {citizen !== null && (
            <button
              onClick={() => setSosOpen((v) => !v)}
              className="text-sm font-bold bg-red-600 text-white rounded-lg px-4 py-2 hover:bg-red-700 shadow-sm"
            >
              {t.mkSos}
            </button>
          )}
        </div>

        <PageIntro k="rasti-im" title={t.myCaseIntroT} body={t.myCaseIntro} />
        {verified && (
          <p className="text-sm bg-emerald-50 text-emerald-700 rounded-lg p-3">{t.mkEmailVerified}</p>
        )}
        {citizen !== null && sosOpen && (
          <SosPanel
            locale={locale}
            onCaseCreated={() => {
              loadCases();
              setVaultKey((k) => k + 1);
            }}
          />
        )}

        {checking ? (
          <Spinner />
        ) : citizen === null ? (
          <Card className="p-6 space-y-4">
            <CitizenAuthForm
              defaultMode="login"
              onAuthed={(c) => {
                setCitizen(c);
                loadCases();
              }}
            />
          </Card>
        ) : cases === null ? (
          <Spinner />
        ) : cases.length === 0 ? (
          <Card className="p-8 text-center space-y-3">
            <p className="text-sm text-slate-500">{t.mkNoCases}</p>
            <Link href="/posto-rastin" className="inline-block text-sm font-medium text-indigo-600 hover:underline">
              {t.mkPostCase} →
            </Link>
          </Card>
        ) : (
          <div className="space-y-4">
            {cases.map((c) => (
              <Card key={c.id} className="p-5 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="text-xs bg-indigo-50 text-indigo-700 rounded-full px-2 py-0.5">
                      {t[c.category as keyof typeof t] as string}
                    </span>
                    {c.urgency === "urgent" && (
                      <span className="ml-1.5 text-xs bg-red-50 text-red-700 rounded-full px-2 py-0.5">
                        {t.mkUrgent}
                      </span>
                    )}
                    {c.urgency === "sos" && (
                      <span className="ml-1.5 text-xs font-bold bg-red-600 text-white rounded-full px-2 py-0.5">
                        SOS
                      </span>
                    )}
                  </div>
                  <span className={`text-xs rounded-full px-2 py-0.5 whitespace-nowrap ${statusStyle(c.status)}`}>
                    {statusLabel[c.status] || c.status}
                  </span>
                </div>
                {c.status !== "closed" && (
                  <CaseTimeline
                    status={c.status}
                    labels={[t.mkStatusOpen, t.mkStatusClaimed, t.mkStatusConverted]}
                  />
                )}
                <p className="text-sm text-slate-700 whitespace-pre-wrap">{c.description}</p>
                {c.claimed_by && (
                  <p className="text-xs text-slate-500">
                    {t.mkClaimedBy}: <span className="font-medium text-slate-700">{c.claimed_by}</span>
                  </p>
                )}
                <div className="flex items-center gap-4 text-sm">
                  {c.status === "claimed" && (
                    <button
                      onClick={() => toggleMessages(c.id)}
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
                  {(c.status === "open" || c.status === "claimed") && (
                    <button onClick={() => closeCase(c.id)} className="text-slate-400 hover:underline">
                      {t.mkCloseCase}
                    </button>
                  )}
                  {c.status === "converted" && (
                    <Link href="/portal" className="text-emerald-600 font-medium hover:underline">
                      {t.mkStatusConverted} →
                    </Link>
                  )}
                </div>
                {c.reviewed && (
                  <p className="text-xs text-emerald-600">{t.rvDone} ✓</p>
                )}
                {c.can_review && <ReviewForm caseId={c.id} onDone={loadCases} />}
                {openCase === c.id && (
                  <div className="border-t border-slate-100 pt-3 space-y-3">
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {messages.length === 0 && (
                        <p className="text-xs text-slate-400">{t.mkMessagesAfterClaim}</p>
                      )}
                      {messages.map((m) => (
                        <div
                          key={m.id}
                          className={`text-sm rounded-lg px-3 py-2 max-w-[85%] ${
                            m.sender === "citizen"
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

        {citizen !== null && <MyBookings />}

        {citizen !== null && <EvidenceVault refreshKey={vaultKey} />}

        {callCase && (
          <VideoCall
            fetchGrant={() => citizenPost<CallGrant>(`/citizen/cases/${callCase}/call-token`)}
            onClose={() => {
              setCallCase(null);
              setVaultKey((k) => k + 1);
            }}
            recordCaseId={callCase}
          />
        )}
      </main>
    </PublicShell>
  );
}

/** Three star-prompts about the service (never the legal outcome). */
function ReviewForm({ caseId, onDone }: { caseId: string; onDone: () => void }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [ratings, setRatings] = useState({ communication: 0, speed: 0, clarity: 0 });
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  const prompts: { key: keyof typeof ratings; label: string }[] = [
    { key: "communication", label: t.rvCommunication },
    { key: "speed", label: t.rvSpeed },
    { key: "clarity", label: t.rvClarity },
  ];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!ratings.communication || !ratings.speed || !ratings.clarity) return;
    setBusy(true);
    setError("");
    try {
      await citizenPost(`/citizen/cases/${caseId}/review`, {
        rating_communication: ratings.communication,
        rating_speed: ratings.speed,
        rating_clarity: ratings.clarity,
        comment: comment.trim() || null,
      });
      setSent(true);
      setTimeout(onDone, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  if (sent) return <p className="text-sm text-emerald-600">{t.rvThanks}</p>;

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="text-sm font-medium text-amber-600 hover:underline"
      >
        ★ {t.rvTitle}
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="border-t border-slate-100 pt-3 space-y-3">
      <p className="text-xs text-slate-500">{t.rvHint}</p>
      {prompts.map((p) => (
        <div key={p.key} className="flex items-center justify-between gap-3">
          <span className="text-sm text-slate-700">{p.label}</span>
          <span className="flex gap-0.5">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setRatings({ ...ratings, [p.key]: n })}
                className={`text-xl leading-none ${
                  n <= ratings[p.key] ? "text-amber-500" : "text-slate-300"
                }`}
                aria-label={`${p.label}: ${n}/5`}
              >
                ★
              </button>
            ))}
          </span>
        </div>
      ))}
      <Textarea
        rows={2}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder={t.rvComment}
        maxLength={1000}
      />
      <ErrorNote message={error} />
      <Button
        type="submit"
        disabled={busy || !ratings.communication || !ratings.speed || !ratings.clarity}
      >
        {busy ? t.loading : t.rvSubmit}
      </Button>
    </form>
  );
}

export default function MyCasePage() {
  return (
    <Suspense fallback={<Spinner />}>
      <MyCaseInner />
    </Suspense>
  );
}

interface MyBooking {
  id: string;
  starts_at: string;
  status: string;
  with: string | null;
}

/** The citizen's consultation reservations (Phase 4 booking). */
function MyBookings() {
  const { t, locale } = useI18n();
  const [bookings, setBookings] = useState<MyBooking[] | null>(null);

  const load = useCallback(() => {
    citizenGet<MyBooking[]>("/citizen/bookings").then(setBookings).catch(() => setBookings([]));
  }, []);

  useEffect(load, [load]);

  if (!bookings || bookings.length === 0) return null;

  const statusLabel: Record<string, string> = {
    pending: t.bkStatusPending,
    confirmed: t.bkStatusConfirmed,
    declined: t.bkStatusDeclined,
    cancelled: t.bkStatusCancelled,
  };
  const statusTone: Record<string, string> = {
    pending: "bg-amber-50 text-amber-700",
    confirmed: "bg-emerald-50 text-emerald-700",
    declined: "bg-red-50 text-red-700",
    cancelled: "bg-slate-100 text-slate-500",
  };

  async function cancel(id: string) {
    try {
      await citizenPost(`/citizen/bookings/${id}/cancel`);
      load();
    } catch {}
  }

  return (
    <Card className="p-5 space-y-3">
      <h2 className="font-semibold flex items-center gap-2">
        <IconCalendar className="h-4 w-4 text-indigo-600" />
        {t.bkMyBookings}
      </h2>
      <div className="space-y-2">
        {bookings.map((b) => (
          <div key={b.id} className="flex items-center justify-between gap-3 flex-wrap text-sm">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-slate-700">
                {new Date(b.starts_at).toLocaleString(locale, {
                  weekday: "short", day: "numeric", month: "short",
                  hour: "2-digit", minute: "2-digit",
                })}
              </span>
              {b.with && <span className="text-slate-500">— {b.with}</span>}
              <span className={`text-xs rounded-full px-2 py-0.5 ${statusTone[b.status] || ""}`}>
                {statusLabel[b.status] || b.status}
              </span>
            </div>
            {(b.status === "pending" || b.status === "confirmed") && (
              <button
                onClick={() => cancel(b.id)}
                className="text-xs text-slate-400 hover:text-red-600 hover:underline"
              >
                {t.bkCancelBooking}
              </button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
