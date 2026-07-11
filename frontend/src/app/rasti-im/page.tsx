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
import { Button, Card, ErrorNote, Input, Label, Spinner, Textarea } from "@/components/ui";
import VideoCall, { CallGrant } from "@/components/video-call";
import PublicShell from "@/components/public-shell";

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

function MyCaseInner() {
  const { t } = useI18n();
  const params = useSearchParams();
  const verifyToken = params.get("verifiko");

  const [citizen, setCitizen] = useState<CitizenInfo | null>(null);
  const [checking, setChecking] = useState(true);
  const [verified, setVerified] = useState(false);
  const [cases, setCases] = useState<CitizenCase[] | null>(null);
  const [login, setLogin] = useState({ email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [openCase, setOpenCase] = useState<string | null>(null);
  const [messages, setMessages] = useState<CaseMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sosOpen, setSosOpen] = useState(params.get("sos") === "1");
  const [sos, setSos] = useState({ description: "", city: "" });
  const [sosSent, setSosSent] = useState(false);
  const [sosBusy, setSosBusy] = useState(false);
  const [sosError, setSosError] = useState("");
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

  async function doLogin(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await citizenPost<{ access_token: string; citizen: CitizenInfo }>(
        "/citizen/login", login
      );
      setCitizenToken(data.access_token);
      setCitizen(data.citizen);
      loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

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

  async function sendSos(e: React.FormEvent) {
    e.preventDefault();
    setSosBusy(true);
    setSosError("");
    try {
      await citizenPost("/citizen/sos", {
        description: sos.description.trim(),
        city: sos.city.trim() || null,
      });
      setSosSent(true);
      setSosOpen(false);
      loadCases();
    } catch (err) {
      setSosError(err instanceof Error ? err.message : t.error);
    } finally {
      setSosBusy(false);
    }
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
          {citizen !== null && !sosSent && (
            <button
              onClick={() => setSosOpen((v) => !v)}
              className="text-sm font-bold bg-red-600 text-white rounded-lg px-4 py-2 hover:bg-red-700 shadow-sm"
            >
              {t.mkSos}
            </button>
          )}
        </div>
        {verified && (
          <p className="text-sm bg-emerald-50 text-emerald-700 rounded-lg p-3">{t.mkEmailVerified}</p>
        )}
        {sosSent && (
          <p className="text-sm bg-red-50 text-red-700 rounded-lg p-3">{t.mkSosSent}</p>
        )}
        {citizen !== null && sosOpen && !sosSent && (
          <Card className="p-5 space-y-3 border-red-200">
            <p className="text-xs text-slate-500">{t.mkSosHint}</p>
            <form onSubmit={sendSos} className="space-y-3">
              <div>
                <Label>{t.mkSosDescribe}</Label>
                <Textarea
                  rows={3}
                  value={sos.description}
                  onChange={(e) => setSos({ ...sos, description: e.target.value })}
                  required
                  minLength={10}
                />
              </div>
              <div>
                <Label>{t.mkCity}</Label>
                <Input
                  value={sos.city}
                  onChange={(e) => setSos({ ...sos, city: e.target.value })}
                />
              </div>
              <ErrorNote message={sosError} />
              <Button type="submit" disabled={sosBusy} className="w-full !bg-red-600 hover:!bg-red-700">
                {sosBusy ? t.loading : t.mkSosSend}
              </Button>
            </form>
          </Card>
        )}

        {checking ? (
          <Spinner />
        ) : citizen === null ? (
          <Card className="p-6 space-y-4">
            <form onSubmit={doLogin} className="space-y-4">
              <div>
                <Label>{t.email}</Label>
                <Input
                  type="email"
                  value={login.email}
                  onChange={(e) => setLogin({ ...login, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label>{t.password}</Label>
                <Input
                  type="password"
                  value={login.password}
                  onChange={(e) => setLogin({ ...login, password: e.target.value })}
                  required
                />
              </div>
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy} className="w-full">
                {busy ? t.loading : t.login}
              </Button>
            </form>
            <p className="text-sm text-center text-slate-500">
              <Link href="/posto-rastin" className="text-indigo-600 hover:underline">
                {t.mkNoAccount}
              </Link>
            </p>
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

        {callCase && (
          <VideoCall
            fetchGrant={() => citizenPost<CallGrant>(`/citizen/cases/${callCase}/call-token`)}
            onClose={() => setCallCase(null)}
          />
        )}
      </main>
    </PublicShell>
  );
}

export default function MyCasePage() {
  return (
    <Suspense fallback={<Spinner />}>
      <MyCaseInner />
    </Suspense>
  );
}
