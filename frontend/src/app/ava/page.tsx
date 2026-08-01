"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { getCitizenToken } from "@/lib/citizen";
import { clientCountry, DE_REGIONS } from "@/lib/country";
import { Button, Card, ErrorNote, Textarea, TypingDots } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import { MicButton, SpeakButton, useVoiceAvailable } from "@/components/voice-controls";
import { IconChat } from "@/components/icons";

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  citations?: { title: string; section: string | null }[];
}

function sessionId(): string {
  let id = localStorage.getItem("avokatim_ava_session");
  if (!id) {
    id = crypto.randomUUID().replace(/-/g, "").slice(0, 32);
    localStorage.setItem("avokatim_ava_session", id);
  }
  return id;
}

export default function PublicAvaPage() {
  const { t, locale } = useI18n();
  const voice = useVoiceAvailable();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");
  const [remaining, setRemaining] = useState<number | null>(null);
  const [limit, setLimit] = useState<number | null>(null);
  const [isCitizen, setIsCitizen] = useState(false);
  const [structuring, setStructuring] = useState(false);
  // DE host: optional Bundesland — widens Ava's sources to that Land's
  // Landesrecht (D-035); remembered in localStorage
  const [isDE, setIsDE] = useState(false);
  const [region, setRegion] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const busyRef = useRef(false);
  const messagesRef = useRef<ChatMsg[]>([]);
  messagesRef.current = messages;
  const regionRef = useRef("");
  regionRef.current = region;

  useEffect(() => {
    if (clientCountry() !== "DE") return;
    setIsDE(true);
    setRegion(localStorage.getItem("avokatim_ava_region") || "");
  }, []);

  function pickRegion(code: string) {
    setRegion(code);
    localStorage.setItem("avokatim_ava_region", code);
  }

  useEffect(() => {
    const headers: Record<string, string> = {};
    const token = getCitizenToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    fetch(`/api/public/ava/quota?session_id=${sessionId()}`, { headers })
      .then((res) => res.json())
      .then((q) => {
        setRemaining(q.remaining);
        setLimit(q.limit);
        setIsCitizen(q.is_citizen);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const askQuestion = useCallback(async (question: string) => {
    if (!question || busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setDraft("");
    const history = messagesRef.current.map((m) => ({ role: m.role, content: m.content }));
    // Append the empty assistant bubble right away: it renders animated
    // typing dots, so the user sees the system working from the first moment
    // (feedback: a static "…" looked like a hang while RAG+LLM warmed up).
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "" },
    ]);

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = getCitizenToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
      const res = await fetch("/api/public/ava/ask-stream", {
        method: "POST",
        headers,
        body: JSON.stringify({
          question, history, session_id: sessionId(), locale,
          region: regionRef.current || undefined,
        }),
      });
      if (!res.ok || !res.body) {
        let detail = t.error;
        try {
          const data = await res.json();
          if (res.status === 429) detail = t.mkAvaLimitReached;
          else if (typeof data.detail === "string") detail = data.detail;
        } catch {}
        // Drop both the user message and the assistant placeholder
        setMessages((prev) => prev.slice(0, -2));
        setDraft(question);
        throw new Error(detail);
      }
      let citations: ChatMsg["citations"] = [];
      let answer = "";
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const raw of events) {
          const line = raw.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          let event: Record<string, unknown>;
          try {
            event = JSON.parse(line.slice(5).trim());
          } catch {
            continue;
          }
          if (event.type === "meta") {
            citations = (event.citations as ChatMsg["citations"]) || [];
            if (typeof event.remaining === "number") setRemaining(event.remaining);
          } else if (event.type === "thinking") {
            setThinking(true);
          } else if (event.type === "delta") {
            setThinking(false);
            answer += event.text as string;
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = { role: "assistant", content: answer, citations };
              return next;
            });
          } else if (event.type === "error") {
            throw new Error(String(event.detail || t.error));
          }
        }
      }
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", content: answer, citations };
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      busyRef.current = false;
      setBusy(false);
      setThinking(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Question typed in the landing hero — ask it right away
  useEffect(() => {
    const prefill = localStorage.getItem("avokatim_ava_prefill");
    if (prefill) {
      localStorage.removeItem("avokatim_ava_prefill");
      askQuestion(prefill.trim());
    }
  }, [askQuestion]);

  function ask(e: React.FormEvent) {
    e.preventDefault();
    askQuestion(draft.trim());
  }

  async function connectToLawyer() {
    // Ava-intake: let the LLM turn the conversation into a structured case
    // draft (category, first-person description, city, urgency). Fall back
    // to the raw user messages if the endpoint is unavailable.
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    if (history.length > 0) {
      setStructuring(true);
      try {
        const res = await fetch("/api/public/ava/structure-case", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ history }),
        });
        if (res.ok) {
          const draft = await res.json();
          localStorage.setItem("avokatim_case_draft", JSON.stringify(draft));
        } else {
          throw new Error("structure failed");
        }
      } catch {
        const userLines = messages.filter((m) => m.role === "user").map((m) => m.content);
        localStorage.setItem("avokatim_case_draft", userLines.join("\n\n").slice(0, 7000));
      } finally {
        setStructuring(false);
      }
    }
    router.push("/posto-rastin");
  }

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t.mkAvaTitle}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.mkAvaIntro}</p>
        </div>

        <PageIntro k="ava" title={t.avaIntroT} body={t.avaIntro} />

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.mkAvaDisclaimer}</p>

        {isDE && (
          <label className="flex items-center gap-2 text-xs text-slate-500">
            <span>{t.avaRegionLabel}</span>
            <select
              value={region}
              onChange={(e) => pickRegion(e.target.value)}
              className="border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-700"
            >
              <option value="">—</option>
              {DE_REGIONS.map((r) => (
                <option key={r.code} value={r.code}>{r.name}</option>
              ))}
            </select>
          </label>
        )}

        {remaining !== null && limit !== null && (
          <p className="text-xs text-slate-400">
            {t.mkAvaRemaining.replace("{n}", String(remaining)).replace("{total}", String(limit))}
            {!isCitizen && (
              <>
                {" — "}
                <Link href="/posto-rastin" className="text-indigo-600 hover:underline">
                  {t.mkAvaSigninForMore}
                </Link>
              </>
            )}
          </p>
        )}

        {/* Empty state: example questions to get started */}
        {messages.length === 0 && !busy && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {t.avaExamplesT}
            </p>
            <div className="flex flex-wrap gap-2">
              {[t.avaEx1, t.avaEx2, t.avaEx3, t.avaEx4, t.avaEx5].map((q) => (
                <button
                  key={q}
                  onClick={() => askQuestion(q)}
                  className="text-left text-sm bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-600 hover:border-indigo-300 hover:text-indigo-700 transition"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex-1 space-y-3">
          {messages.map((m, i) => (
            <div key={i} className={m.role === "assistant" ? "flex items-start gap-2.5" : ""}>
              {m.role === "assistant" && (
                <span className="h-8 w-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                  <IconChat className="h-4 w-4" />
                </span>
              )}
              <div className={m.role === "assistant" ? "min-w-0 flex-1" : ""}>
              <div
                className={`text-sm rounded-xl px-4 py-3 whitespace-pre-wrap max-w-[90%] ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white ml-auto"
                    : "bg-white border border-slate-200 text-slate-700"
                }`}
              >
                {m.content || <TypingDots />}
              </div>
              {m.role === "assistant" && (m.content || (m.citations && m.citations.length > 0)) && (
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  {m.content && !busy && (
                    <SpeakButton text={m.content} locale={locale} serverTts={voice.tts} />
                  )}
                  {(m.citations || []).slice(0, 6).map((c, j) => (
                    <span key={j} className="text-[11px] bg-slate-100 text-slate-500 rounded-full px-2 py-0.5">
                      {c.title}{c.section ? `, ${c.section}` : ""}
                    </span>
                  ))}
                </div>
              )}
              </div>
            </div>
          ))}
          {thinking && (
            <p className="flex items-center gap-2 text-xs text-slate-400">
              <TypingDots /> {t.avaThinking}
            </p>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length > 0 && (
          <Card className="p-4 flex items-center justify-between gap-3 flex-wrap">
            <p className="text-sm text-slate-600">{t.mkAvaConnectHint}</p>
            <Button onClick={connectToLawyer} disabled={structuring}>
              {structuring ? t.loading : t.mkAvaConnectLawyer}
            </Button>
          </Card>
        )}

        <ErrorNote message={error} />
        <form onSubmit={ask} className="flex gap-2 items-end sticky bottom-24 md:bottom-4">
          <Textarea
            rows={2}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={t.mkAvaPlaceholder}
            className="flex-1 bg-white shadow-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                ask(e);
              }
            }}
          />
          {voice.stt && (
            <MicButton
              locale={locale}
              disabled={busy}
              onText={(text) => setDraft((d) => (d ? `${d} ${text}` : text))}
            />
          )}
          <Button type="submit" disabled={busy || !draft.trim()}>
            {busy ? t.loading : t.mkSend}
          </Button>
        </form>
      </main>
    </PublicShell>
  );
}
