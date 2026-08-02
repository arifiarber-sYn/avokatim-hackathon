"use client";

/**
 * Contextual assistant panel for the lawyer app (D-052). Follows the pattern
 * Clio ("Manage AI"), Smokeball ("Archie") and AnNoText ("Expert AI")
 * converged on: a persistent launcher + a right-hand slide-over that KNOWS
 * which matter you are viewing — no floating consumer bubble, no page switch.
 *
 * Kept intentionally lean: legal mode with streaming + deep research + voice.
 * Conversation list and office mode stay on the full /assistant page.
 * The component stays mounted (visibility toggled) so an ongoing conversation
 * survives closing and reopening the panel while navigating the app.
 */
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { apiGet, apiStream } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Matter, Message } from "@/lib/types";
import { Button, ErrorNote, Textarea } from "@/components/ui";
import { MicButton, SpeakButton, useVoiceAvailable } from "@/components/voice-controls";
import { IconChat } from "@/components/icons";

const MATTER_ROUTE = /^\/matters\/([0-9a-f-]{16,})/i;

export default function AssistantPanel() {
  const { t, locale } = useI18n();
  const voice = useVoiceAvailable();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [deep, setDeep] = useState(false);
  const [steps, setSteps] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [provider, setProvider] = useState("deepseek");
  const [externalAllowed, setExternalAllowed] = useState(true);
  // Matter context: when the lawyer is on /matters/[id], the panel scopes
  // Ava to that matter automatically and shows it as a removable chip.
  const [ctxMatter, setCtxMatter] = useState<Matter | null>(null);
  const [scopeOn, setScopeOn] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const providersLoaded = useRef(false);

  useEffect(() => {
    if (!open || providersLoaded.current) return;
    providersLoaded.current = true;
    apiGet<{ external_ai_allowed: boolean }>("/assistant/providers")
      .then((r) => {
        setExternalAllowed(r.external_ai_allowed);
        if (!r.external_ai_allowed) setProvider("local");
      })
      .catch(() => {});
  }, [open]);

  useEffect(() => {
    const m = pathname.match(MATTER_ROUTE);
    if (!m) {
      setCtxMatter(null);
      return;
    }
    setScopeOn(true);
    apiGet<Matter>(`/matters/${m[1]}`)
      .then(setCtxMatter)
      .catch(() => setCtxMatter(null));
  }, [pathname]);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  // Escape closes the panel
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const matterId = scopeOn && ctxMatter ? ctxMatter.id : null;

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
      await apiStream(
        deep ? "/assistant/deep-research" : "/assistant/ask-stream",
        {
          question: q,
          matter_id: matterId,
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
          } else if (ev.type === "done") {
            finalMessage = ev.message as unknown as Message;
          } else if (ev.type === "error") {
            errorDetail = (ev.detail as string) || null;
          }
        }
      );
      if (errorDetail) throw new Error(errorDetail);
      if (!finalMessage) throw new Error(t.error);
      const reply = finalMessage as Message;
      if (newConversationId) setConversationId(newConversationId);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== "tmp" && m.id !== "streaming"),
        { id: "user-" + Date.now(), role: "user", content: q, citations: [], created_at: new Date().toISOString() },
        reply,
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setMessages((prev) => prev.filter((m) => m.id !== "tmp" && m.id !== "streaming"));
      setQuestion(q);
    } finally {
      setBusy(false);
      setSteps([]);
    }
  }

  // On /assistant the full page already is the assistant
  if (pathname.startsWith("/assistant")) return null;

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          aria-label={t.avaFabLabel}
          className="fixed z-40 right-4 bottom-20 md:bottom-6 inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 text-white pl-3.5 pr-4 py-3 shadow-lg shadow-indigo-300/50 hover:shadow-xl hover:-translate-y-0.5 transition-all"
          style={{ marginBottom: "env(safe-area-inset-bottom)" }}
        >
          <span className="relative">
            <IconChat className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          </span>
          <span className="text-sm font-bold">Ava</span>
          <span className="text-[10px] font-semibold bg-white/20 rounded-full px-1.5 py-0.5">AI</span>
        </button>
      )}

      {/* hidden (not unmounted) so the conversation survives close/reopen */}
      <div
        className={`fixed inset-0 z-50 md:inset-auto md:right-4 md:bottom-4 md:top-auto md:w-[440px] md:h-[min(680px,calc(100vh-3rem))] bg-white md:rounded-2xl md:shadow-2xl md:ring-1 md:ring-slate-200 flex-col overflow-hidden ${
          open ? "flex" : "hidden"
        }`}
        role="dialog"
        aria-label={t.assistant}
      >
        <div className="flex items-center justify-between gap-3 px-4 py-3 bg-slate-900 text-white shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="h-8 w-8 rounded-full bg-indigo-500/25 text-indigo-300 flex items-center justify-center shrink-0">
              <IconChat className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-bold truncate">Ava · {t.assistant}</p>
              <Link href="/assistant" onClick={() => setOpen(false)} className="text-[11px] text-indigo-300 hover:underline">
                {t.apOpenFull} →
              </Link>
            </div>
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label={t.close}
            className="h-8 w-8 rounded-full hover:bg-white/15 flex items-center justify-center text-xl leading-none shrink-0"
          >
            ×
          </button>
        </div>

        {/* Context strip: matter scope + deep research + transparency */}
        <div className="px-4 py-2 border-b border-slate-100 flex items-center gap-2 flex-wrap shrink-0">
          {ctxMatter && scopeOn && (
            <span
              title={t.apMatterCtx}
              className="inline-flex items-center gap-1.5 text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full pl-2.5 pr-1 py-0.5 max-w-[220px]"
            >
              <span className="truncate">{ctxMatter.reference} — {ctxMatter.title}</span>
              <button
                onClick={() => setScopeOn(false)}
                aria-label={t.close}
                className="h-4 w-4 rounded-full hover:bg-indigo-100 flex items-center justify-center leading-none"
              >
                ×
              </button>
            </span>
          )}
          <label
            className={`inline-flex items-center gap-1.5 text-[11px] rounded-full border px-2.5 py-0.5 cursor-pointer select-none ${
              deep
                ? "bg-indigo-50 border-indigo-300 text-indigo-800"
                : "border-slate-200 text-slate-500 hover:bg-slate-50"
            }`}
            title={t.deepResearchHint}
          >
            <input
              type="checkbox"
              checked={deep}
              onChange={(e) => setDeep(e.target.checked)}
              className="accent-indigo-600 h-3 w-3"
            />
            🔎 {t.deepResearch}
          </label>
          {/* International-transfer transparency (Law 06/L-082 art. 49) */}
          {!externalAllowed ? (
            <span className="text-[11px] text-slate-400">🔒 {t.providerLocal}</span>
          ) : provider !== "local" ? (
            <span className="text-[11px] text-amber-600" title={t.externalAiNotice}>⚠ {t.providerExternal}</span>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && !busy && (
            <div className="text-center py-14">
              <p className="text-3xl mb-2">✦</p>
              <p className="text-slate-500 text-sm">{t.askAva}</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={m.id + i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] ${m.role === "user" ? "" : "space-y-1"}`}>
                <div
                  className={`rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
                    m.role === "user" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-900"
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
                          {c.reference && !c.title.includes(c.reference) ? ` (${c.reference})` : ""}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                {m.role === "assistant" && m.id !== "streaming" && m.content && (
                  <SpeakButton text={m.content} locale={locale} serverTts={voice.tts} />
                )}
              </div>
            </div>
          ))}
          {busy && steps.length > 0 && (
            <div className="text-xs text-slate-500 bg-indigo-50/60 border border-indigo-100 rounded-xl px-3.5 py-2.5 space-y-1">
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

        <form
          onSubmit={send}
          className="p-3 border-t border-slate-100 space-y-2 shrink-0"
          style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
        >
          <ErrorNote message={error} />
          <div className="flex gap-2 items-end">
            <Textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={t.askAva}
              className="flex-1"
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
      </div>
    </>
  );
}
