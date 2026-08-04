"use client";

import { useEffect, useRef, useState } from "react";
import { apiGet, apiPost, apiStream } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import { MicButton, SpeakButton, useVoiceAvailable } from "@/components/voice-controls";
import CitationChecks, { CitationCheck } from "@/components/citation-checks";
import { Conversation, Matter, Message } from "@/lib/types";
import { Button, Card, ErrorNote, Select, Textarea } from "@/components/ui";

interface Provider {
  name: string;
  configured: boolean;
}

export default function AssistantPage() {
  const { t, locale } = useI18n();
  const voice = useVoiceAvailable();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState("");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [externalAllowed, setExternalAllowed] = useState(true);
  const [provider, setProvider] = useState("deepseek");
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [deep, setDeep] = useState(false);
  const [steps, setSteps] = useState<string[]>([]);
  const [mode, setMode] = useState<"legal" | "office">("legal");
  // Per-message citation verification results (D-059 F6)
  const [checks, setChecks] = useState<Record<string, CitationCheck[]>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiGet<Conversation[]>("/assistant/conversations").then(setConversations).catch(() => {});
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => {});
    apiGet<{ providers: Provider[]; external_ai_allowed: boolean }>("/assistant/providers")
      .then((r) => {
        setProviders(r.providers);
        setExternalAllowed(r.external_ai_allowed);
        if (!r.external_ai_allowed) setProvider("local");
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (conversationId) {
      apiGet<Message[]>(`/assistant/conversations/${conversationId}/messages`)
        .then(setMessages)
        .catch(() => {});
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || busy) return;
    const q = question;
    setQuestion("");
    setBusy(true);
    setError("");
    setMessages((prev) => [
      ...prev,
      { id: "tmp", role: "user", content: q, citations: [], created_at: new Date().toISOString() },
    ]);
    try {
      let streamed = "";
      let newConversationId: string | null = null;
      let finalMessage: Message | null = null;
      let errorDetail: string | null = null;
      let citationChecks: CitationCheck[] = [];
      await apiStream(
        deep ? "/assistant/deep-research" : "/assistant/ask-stream",
        {
          question: q,
          matter_id: matterId || null,
          conversation_id: conversationId,
          provider,
          locale,
        },
        (ev) => {
          if (ev.type === "meta") {
            newConversationId = ev.conversation_id as string;
          } else if (ev.type === "step") {
            if (ev.step === "subquestions" && ev.status === "start") {
              setSteps([t.drSubq]);
            } else if (ev.step === "search") {
              setSteps((prev) => [
                ...prev,
                `${t.drSearch} (${ev.index as number}/${ev.total as number}): ${ev.question as string}`,
              ]);
            } else if (ev.step === "synthesis") {
              setSteps((prev) => [...prev, t.drSynth]);
            }
          } else if (ev.type === "delta") {
            streamed += ev.text as string;
            const text = streamed;
            setMessages((prev) => [
              ...prev.filter((m) => m.id !== "streaming"),
              { id: "streaming", role: "assistant", content: text, citations: [], created_at: new Date().toISOString() },
            ]);
          } else if (ev.type === "citation_check") {
            citationChecks = ev.citations as CitationCheck[];
          } else if (ev.type === "done") {
            finalMessage = ev.message as unknown as Message;
          } else if (ev.type === "error") {
            errorDetail = (ev.detail as string) || null;
          }
        }
      );
      if (errorDetail) throw new Error(errorDetail);
      if (!finalMessage) throw new Error(t.error);
      // TS cannot see assignments made inside the stream callback
      const reply = finalMessage as Message;
      if (citationChecks.length) setChecks((prev) => ({ ...prev, [reply.id]: citationChecks }));
      if (newConversationId) setConversationId(newConversationId);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== "tmp" && m.id !== "streaming"),
        { id: "user-" + Date.now(), role: "user", content: q, citations: [], created_at: new Date().toISOString() },
        reply,
      ]);
      apiGet<Conversation[]>("/assistant/conversations").then(setConversations).catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setMessages((prev) => prev.filter((m) => m.id !== "tmp" && m.id !== "streaming"));
      setQuestion(q);
    } finally {
      setBusy(false);
      setSteps([]);
    }
  }

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-9rem)] md:h-[calc(100vh-6rem)]">
      <PageIntro k="assistant" title={t.assistantIntroT} body={t.assistantIntro} />
      <div className="flex gap-2">
        {(
          [
            { key: "legal", label: t.oaModeLegal },
            { key: "office", label: t.oaModeOffice },
          ] as const
        ).map((m) => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={`text-sm font-medium rounded-lg px-4 py-1.5 border transition ${
              mode === m.key
                ? "bg-indigo-600 border-indigo-600 text-white"
                : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>
      {mode === "office" ? (
        <OfficeTab provider={provider} />
      ) : (
      <div className="flex gap-6 flex-1 min-h-0">
      <div className="hidden md:block w-64 shrink-0 space-y-3 overflow-auto">
        <Button
          className="w-full"
          variant="secondary"
          onClick={() => {
            setConversationId(null);
            setMessages([]);
          }}
        >
          {t.newConversation}
        </Button>
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => setConversationId(c.id)}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate ${
              conversationId === c.id ? "bg-indigo-100 text-indigo-800" : "hover:bg-slate-100"
            }`}
          >
            {c.title || "…"}
          </button>
        ))}
      </div>

      <Card className="flex-1 flex flex-col min-w-0">
        {/* Mobile: conversation picker replaces the sidebar list */}
        <div className="md:hidden flex gap-2 p-3 border-b border-slate-100">
          <div className="flex-1 min-w-0">
            <Select
              value={conversationId || ""}
              onChange={(e) => {
                if (e.target.value) setConversationId(e.target.value);
                else {
                  setConversationId(null);
                  setMessages([]);
                }
              }}
            >
              <option value="">{t.newConversation}</option>
              {conversations.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title || "…"}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <div className="flex gap-3 p-4 border-b border-slate-100 flex-wrap">
          <div className="flex-1 min-w-48">
            <Select value={matterId} onChange={(e) => setMatterId(e.target.value)}>
              <option value="">{t.noMatter}</option>
              {matters.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.reference} — {m.title}
                </option>
              ))}
            </Select>
          </div>
          <div className="w-full sm:w-56">
            <Select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              disabled={!externalAllowed}
            >
              {providers.map((p) => (
                <option
                  key={p.name}
                  value={p.name}
                  disabled={!p.configured || (p.name !== "local" && !externalAllowed)}
                >
                  {p.name === "deepseek" ? t.providerExternal : t.providerLocal}
                  {!p.configured ? " (—)" : ""}
                </option>
              ))}
            </Select>
          </div>
          <label
            className={`flex items-center gap-2 text-sm rounded-lg border px-3 py-2 cursor-pointer select-none ${
              deep
                ? "bg-indigo-50 border-indigo-300 text-indigo-800"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
            title={t.deepResearchHint}
          >
            <input
              type="checkbox"
              checked={deep}
              onChange={(e) => setDeep(e.target.checked)}
              className="accent-indigo-600"
            />
            🔎 {t.deepResearch}
          </label>
          {deep && (
            <p className="w-full text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2">
              {t.deepResearchHint}
            </p>
          )}
          {/* International-transfer transparency (Law 06/L-082 art. 49) */}
          {!externalAllowed ? (
            <p className="w-full text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
              🔒 {t.externalAiOff}
            </p>
          ) : provider !== "local" ? (
            <p className="w-full text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              ⚠ {t.externalAiNotice}
            </p>
          ) : null}
        </div>

        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">✦</p>
              <p className="text-slate-500 text-sm">{t.askAva}</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={m.id + i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] ${m.role === "user" ? "" : "space-y-1"}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
                    m.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 text-slate-900"
                  }`}
                >
                  {m.content}
                  {m.citations?.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-300/50 text-xs opacity-80">
                      <p className="font-semibold">{t.citations}:</p>
                      {m.citations.map((c, j) => (
                        <p key={j}>
                          • {c.title}
                          {c.section ? `, ${c.section}` : ""}
                          {c.reference && !c.title.includes(c.reference)
                            ? ` (${c.reference})`
                            : ""}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                {m.role === "assistant" && <CitationChecks checks={checks[m.id]} />}
                {m.role === "assistant" && m.id !== "streaming" && m.content && (
                  <SpeakButton text={m.content} locale={locale} serverTts={voice.tts} />
                )}
              </div>
            </div>
          ))}
          {busy && steps.length > 0 && (
            <div className="text-xs text-slate-500 bg-indigo-50/60 border border-indigo-100 rounded-xl px-4 py-3 space-y-1">
              <p className="font-semibold text-indigo-700">{t.deepResearch}</p>
              {steps.map((s, i) => (
                <p key={i} className={i === steps.length - 1 ? "animate-pulse" : ""}>
                  {i === steps.length - 1 ? "→" : "✓"} {s}
                </p>
              ))}
            </div>
          )}
          {busy && steps.length === 0 && !messages.some((m) => m.id === "streaming") && (
            <p className="text-sm text-slate-400 animate-pulse">{t.thinking}</p>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={send} className="p-4 border-t border-slate-100 space-y-2">
          <ErrorNote message={error} />
          <div className="flex gap-2">
            <Textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={t.askAva}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(e);
                }
              }}
            />
            {voice.stt && (
              <MicButton
                locale={locale}
                disabled={busy}
                onText={(text) => setQuestion((q) => (q ? `${q} ${text}` : text))}
              />
            )}
            <Button type="submit" disabled={busy || !question.trim()}>
              {t.send}
            </Button>
          </div>
        </form>
      </Card>
      </div>
      )}
    </div>
  );
}

interface OfficeAnswer {
  answer: string | null;
  tool: string | null;
  data: Record<string, unknown>[];
}

function OfficeTab({ provider }: { provider: string }) {
  const { t, locale } = useI18n();
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<{ q: string; a: OfficeAnswer }[]>([]);
  const chips = [t.oaChip1, t.oaChip2, t.oaChip3, t.oaChip4, t.oaChip5, t.oaChip6];

  async function ask(q: string) {
    if (!q.trim() || busy) return;
    setBusy(true);
    setError("");
    setQuestion("");
    try {
      const res = await apiPost<OfficeAnswer>("/assistant/office-ask", {
        question: q,
        language: locale,
        provider,
      });
      setHistory((prev) => [...prev, { q, a: res }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setQuestion(q);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex-1 flex flex-col min-h-0">
      <div className="p-4 border-b border-slate-100 space-y-2">
        <p className="text-sm text-slate-600">{t.oaHint}</p>
        <div className="flex flex-wrap gap-1.5">
          {chips.map((c) => (
            <button
              key={c}
              onClick={() => ask(c)}
              disabled={busy}
              className="text-xs rounded-full px-3 py-1.5 border bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-700 transition disabled:opacity-50"
            >
              {c}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {history.length === 0 && !busy && (
          <div className="text-center py-16">
            <p className="text-4xl mb-3">📊</p>
            <p className="text-slate-500 text-sm">{t.oaEmpty}</p>
          </div>
        )}
        {history.map((h, i) => (
          <div key={i} className="space-y-2">
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl px-4 py-3 text-sm bg-indigo-600 text-white">
                {h.q}
              </div>
            </div>
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-2xl px-4 py-3 text-sm bg-slate-100 text-slate-900 whitespace-pre-wrap leading-relaxed">
                {h.a.answer || t.oaNoTool}
              </div>
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-slate-400 animate-pulse">{t.thinking}</p>}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
        className="p-4 border-t border-slate-100 space-y-2"
      >
        <ErrorNote message={error} />
        <div className="flex gap-2">
          <Textarea
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={t.oaPlaceholder}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                ask(question);
              }
            }}
          />
          <Button type="submit" disabled={busy || !question.trim()}>
            {t.send}
          </Button>
        </div>
      </form>
    </Card>
  );
}
