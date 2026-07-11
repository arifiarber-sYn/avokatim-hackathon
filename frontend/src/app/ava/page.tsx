"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { getCitizenToken } from "@/lib/citizen";
import { Button, Card, ErrorNote, LocaleSwitcher, Textarea } from "@/components/ui";

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
  const { t } = useI18n();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");
  const [remaining, setRemaining] = useState<number | null>(null);
  const [limit, setLimit] = useState<number | null>(null);
  const [isCitizen, setIsCitizen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

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

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    const question = draft.trim();
    if (!question || busy) return;
    setBusy(true);
    setError("");
    setDraft("");
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = getCitizenToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
      const res = await fetch("/api/public/ava/ask-stream", {
        method: "POST",
        headers,
        body: JSON.stringify({ question, history, session_id: sessionId() }),
      });
      if (!res.ok || !res.body) {
        let detail = t.error;
        try {
          const data = await res.json();
          if (res.status === 429) detail = t.mkAvaLimitReached;
          else if (typeof data.detail === "string") detail = data.detail;
        } catch {}
        setMessages((prev) => prev.slice(0, -1));
        setDraft(question);
        throw new Error(detail);
      }
      let citations: ChatMsg["citations"] = [];
      let answer = "";
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
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
      setBusy(false);
      setThinking(false);
    }
  }

  function connectToLawyer() {
    // Prefill the case form from the conversation
    const userLines = messages.filter((m) => m.role === "user").map((m) => m.content);
    if (userLines.length > 0) {
      localStorage.setItem("avokatim_case_draft", userLines.join("\n\n").slice(0, 7000));
    }
    router.push("/posto-rastin");
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-indigo-700">
            Avokat<span className="text-slate-900">IM</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/avokatet" className="text-sm text-slate-600 hover:underline">
              {t.mkLawyersDirectory}
            </Link>
            <LocaleSwitcher />
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t.mkAvaTitle}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.mkAvaIntro}</p>
        </div>

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.mkAvaDisclaimer}</p>

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

        <div className="flex-1 space-y-3">
          {messages.map((m, i) => (
            <div key={i}>
              <div
                className={`text-sm rounded-xl px-4 py-3 whitespace-pre-wrap max-w-[90%] ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white ml-auto"
                    : "bg-white border border-slate-200 text-slate-700"
                }`}
              >
                {m.content || "…"}
              </div>
              {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {m.citations.slice(0, 6).map((c, j) => (
                    <span key={j} className="text-[11px] bg-slate-100 text-slate-500 rounded-full px-2 py-0.5">
                      {c.title}{c.section ? `, ${c.section}` : ""}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {thinking && <p className="text-xs text-slate-400 animate-pulse">…</p>}
          <div ref={bottomRef} />
        </div>

        {messages.length > 0 && (
          <Card className="p-4 flex items-center justify-between gap-3 flex-wrap">
            <p className="text-sm text-slate-600">{t.mkAvaConnectHint}</p>
            <Button onClick={connectToLawyer}>{t.mkAvaConnectLawyer}</Button>
          </Card>
        )}

        <ErrorNote message={error} />
        <form onSubmit={ask} className="flex gap-2 items-end sticky bottom-4">
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
          <Button type="submit" disabled={busy || !draft.trim()}>
            {busy ? t.loading : t.mkSend}
          </Button>
        </form>
      </main>
    </div>
  );
}
