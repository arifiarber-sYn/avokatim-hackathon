"use client";

import { useEffect, useRef, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Conversation, Matter, Message } from "@/lib/types";
import { Button, Card, ErrorNote, Select, Textarea } from "@/components/ui";

interface Provider {
  name: string;
  configured: boolean;
}

export default function AssistantPage() {
  const { t } = useI18n();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState("");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [provider, setProvider] = useState("deepseek");
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiGet<Conversation[]>("/assistant/conversations").then(setConversations).catch(() => {});
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => {});
    apiGet<Provider[]>("/assistant/providers").then(setProviders).catch(() => {});
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
      const result = await apiPost<{ conversation_id: string; message: Message }>(
        "/assistant/ask",
        {
          question: q,
          matter_id: matterId || null,
          conversation_id: conversationId,
          provider,
        }
      );
      setConversationId(result.conversation_id);
      setMessages((prev) => [...prev.filter((m) => m.id !== "tmp"), 
        { id: "user-" + Date.now(), role: "user", content: q, citations: [], created_at: new Date().toISOString() },
        result.message]);
      apiGet<Conversation[]>("/assistant/conversations").then(setConversations).catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setMessages((prev) => prev.filter((m) => m.id !== "tmp"));
      setQuestion(q);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-9rem)] md:h-[calc(100vh-6rem)]">
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
            <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
              {providers.map((p) => (
                <option key={p.name} value={p.name} disabled={!p.configured}>
                  {p.name === "deepseek" ? t.providerExternal : t.providerLocal}
                  {!p.configured ? " (—)" : ""}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">✦</p>
              <p className="text-slate-500 text-sm">{t.askBora}</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={m.id + i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
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
                        {c.reference ? ` (${c.reference})` : ""}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {busy && <p className="text-sm text-slate-400 animate-pulse">{t.thinking}</p>}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={send} className="p-4 border-t border-slate-100 space-y-2">
          <ErrorNote message={error} />
          <div className="flex gap-2">
            <Textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={t.askBora}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(e);
                }
              }}
            />
            <Button type="submit" disabled={busy || !question.trim()}>
              {t.send}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
