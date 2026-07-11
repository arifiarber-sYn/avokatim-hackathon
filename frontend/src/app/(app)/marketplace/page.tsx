"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Spinner, Textarea } from "@/components/ui";

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

  const load = useCallback(() => {
    apiGet<OpenCase[]>("/marketplace/cases").then(setOpenCases).catch(() => setOpenCases([]));
    apiGet<MyCase[]>("/marketplace/cases/mine").then(setMyCases).catch(() => setMyCases([]));
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
      setError(err instanceof Error ? err.message : t.error);
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
      <div>
        <h1 className="text-2xl font-bold">{t.marketplace}</h1>
        <p className="text-sm text-slate-500 mt-1">{t.mkPublicProfileHint}</p>
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
                    {c.directed_to_me && (
                      <span className="text-xs bg-amber-50 text-amber-700 rounded-full px-2 py-0.5">
                        {t.mkDirectedToYou}
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
                <Link href="/intake" className="text-slate-500 hover:underline">
                  {t.mkGoToIntake}
                </Link>
              </div>
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
    </div>
  );
}
