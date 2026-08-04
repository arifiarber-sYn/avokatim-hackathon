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
import { apiGet, apiPost, apiStream } from "@/lib/api";
import { haptic } from "@/lib/haptics";
import { useI18n } from "@/lib/i18n";
import { track } from "@/lib/analytics";
import { Matter, Message } from "@/lib/types";
import { Button, ErrorNote, Textarea } from "@/components/ui";
import { MicButton, SpeakButton, useVoiceAvailable } from "@/components/voice-controls";
import CitationChecks, { CitationCheck } from "@/components/citation-checks";
import { IconChat } from "@/components/icons";

const MATTER_ROUTE = /^\/matters\/([0-9a-f-]{16,})/i;

/** Deadline proposal from POST /assistant/actions/extract-deadlines. */
interface DeadlineProposal {
  title: string;
  kind: string;
  due_date: string | null;
  trigger_date: string | null;
  days: number | null;
  legal_basis: string | null;
  confidence: string;
}

/** One in-flight approval flow at a time, anchored to a message index. */
type ActionState =
  | { type: "deadlines"; msgIdx: number; busy: boolean; proposals: DeadlineProposal[] | null; selected: boolean[] }
  | { type: "draft"; msgIdx: number; busy: boolean; title: string };

/** Ava Agent (D-054): visible work plan streamed from /assistant/agent-run. */
interface AgentStep {
  label: string;
  status: "pending" | "running" | "done" | "failed";
}

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
  // Action execution with approval (D-053): Ava proposes, the lawyer confirms
  const [action, setAction] = useState<ActionState | null>(null);
  const [notice, setNotice] = useState("");
  // Per-message citation verification results (D-059 F6)
  const [checks, setChecks] = useState<Record<string, CitationCheck[]>>({});
  // Ava Agent mode (D-054): goal → visible plan → step-by-step execution
  const [agentMode, setAgentMode] = useState(false);
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const providersLoaded = useRef(false);

  // "Ask Ava" row in the global search dispatches this event (D-053)
  useEffect(() => {
    const onAsk = (e: Event) => {
      const q = (e as CustomEvent<{ question?: string }>).detail?.question;
      setOpen(true);
      if (q) setQuestion(q);
    };
    window.addEventListener("avokatim:ask-ava", onAsk);
    return () => window.removeEventListener("avokatim:ask-ava", onAsk);
  }, []);

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

  async function runAgent(goal: string) {
    if (!matterId) return;
    track("agent_run");
    setBusy(true);
    setError("");
    setNotice("");
    setAgentSteps([]);
    setMessages((prev) => [
      ...prev,
      { id: "user-" + Date.now(), role: "user", content: goal, citations: [], created_at: new Date().toISOString() },
    ]);
    try {
      let errorDetail: string | null = null;
      await apiStream(
        "/assistant/agent-run",
        { matter_id: matterId, goal, provider, locale },
        (ev) => {
          if (ev.type === "plan") {
            const steps = ev.steps as { label: string }[];
            setAgentSteps(steps.map((s) => ({ label: s.label, status: "pending" })));
          } else if (ev.type === "step") {
            const idx = ev.index as number;
            const status = ev.status as AgentStep["status"];
            setAgentSteps((prev) => prev.map((s, i) => (i === idx ? { ...s, status } : s)));
          } else if (ev.type === "result") {
            const msg: Message = {
              id: "agent-" + Date.now() + Math.random(),
              role: "assistant",
              content: ev.content as string,
              citations: (ev.citations as Message["citations"]) || [],
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, msg]);
          } else if (ev.type === "approval") {
            if (ev.kind === "deadlines") {
              const proposals = (ev.proposals as DeadlineProposal[]) || [];
              setMessages((prev) => {
                const msg: Message = {
                  id: "agent-" + Date.now() + Math.random(),
                  role: "assistant",
                  content: t.apActExtract,
                  citations: [],
                  created_at: new Date().toISOString(),
                };
                const next = [...prev, msg];
                setAction({
                  type: "deadlines", msgIdx: next.length - 1, busy: false,
                  proposals, selected: proposals.map((p) => Boolean(p.due_date)),
                });
                return next;
              });
            } else if (ev.kind === "draft") {
              const content = ev.content as string;
              setMessages((prev) => {
                const msg: Message = {
                  id: "agent-" + Date.now() + Math.random(),
                  role: "assistant",
                  content,
                  citations: [],
                  created_at: new Date().toISOString(),
                };
                const next = [...prev, msg];
                setAction({
                  type: "draft", msgIdx: next.length - 1, busy: false,
                  title: ((ev.title as string) || t.apActDraft).slice(0, 120),
                });
                return next;
              });
            }
          } else if (ev.type === "error") {
            errorDetail = (ev.detail as string) || null;
          }
        }
      );
      if (errorDetail) throw new Error(errorDetail);
      setAgentSteps((prev) =>
        prev.map((s) => (s.status === "running" || s.status === "pending" ? { ...s, status: "done" } : s))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || busy) return;
    const q = question;
    setQuestion("");
    if (agentMode && matterId) {
      await runAgent(q);
      return;
    }
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
      const reply = finalMessage as Message;
      if (citationChecks.length) setChecks((prev) => ({ ...prev, [reply.id]: citationChecks }));
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

  async function extractDeadlines(msgIdx: number, text: string) {
    if (!matterId) return;
    setNotice("");
    setError("");
    setAction({ type: "deadlines", msgIdx, busy: true, proposals: null, selected: [] });
    try {
      const proposals = await apiPost<DeadlineProposal[]>(
        "/assistant/actions/extract-deadlines",
        { matter_id: matterId, text }
      );
      setAction({
        type: "deadlines", msgIdx, busy: false, proposals,
        // pre-select only the ones with a concrete date (bulk skips the rest)
        selected: proposals.map((p) => Boolean(p.due_date)),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setAction(null);
    }
  }

  async function createSelectedDeadlines() {
    if (!matterId || !action || action.type !== "deadlines" || !action.proposals) return;
    const chosen = action.proposals.filter((_, i) => action.selected[i] && action.proposals![i].due_date);
    if (chosen.length === 0) return;
    setAction({ ...action, busy: true });
    try {
      const res = await apiPost<{ created: number }>(
        `/matters/${matterId}/deadlines/bulk`,
        { deadlines: chosen }
      );
      haptic([15, 30, 15]);
      setNotice(t.apActDlDone.replace("{n}", String(res.created)));
      setAction(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setAction({ ...action, busy: false });
    }
  }

  async function saveDraft() {
    if (!matterId || !ctxMatter || !action || action.type !== "draft") return;
    const msg = messages[action.msgIdx];
    if (!msg || !action.title.trim()) return;
    setAction({ ...action, busy: true });
    try {
      await apiPost("/assistant/actions/save-draft", {
        matter_id: matterId,
        title: action.title.trim(),
        content: msg.content,
      });
      haptic([15, 30, 15]);
      setNotice(t.apActDraftDone);
      setAction(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
      setAction({ ...action, busy: false });
    }
  }

  // On /assistant the full page already is the assistant
  if (pathname.startsWith("/assistant")) return null;

  return (
    <>
      {!open && (
        <button
          onClick={() => {
            haptic();
            setOpen(true);
          }}
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
          {/* Ava Agent (D-054): only with a matter in scope */}
          {matterId && (
            <label
              className={`inline-flex items-center gap-1.5 text-[11px] rounded-full border px-2.5 py-0.5 cursor-pointer select-none ${
                agentMode
                  ? "bg-violet-50 border-violet-300 text-violet-800"
                  : "border-slate-200 text-slate-500 hover:bg-slate-50"
              }`}
              title={t.agModeHint}
            >
              <input
                type="checkbox"
                checked={agentMode}
                onChange={(e) => setAgentMode(e.target.checked)}
                className="accent-violet-600 h-3 w-3"
              />
              🤖 {t.agMode}
            </label>
          )}
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
                {m.role === "assistant" && <CitationChecks checks={checks[m.id]} />}
                {m.role === "assistant" && m.id !== "streaming" && m.content && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <SpeakButton text={m.content} locale={locale} serverTts={voice.tts} />
                    {/* Action execution with approval (D-053) — only with a matter in scope */}
                    {matterId && (
                      <>
                        <button
                          onClick={() => extractDeadlines(i, m.content)}
                          disabled={busy || Boolean(action?.busy)}
                          className="text-[11px] rounded-full border border-slate-200 px-2.5 py-1 text-slate-600 hover:border-indigo-300 hover:text-indigo-700 transition disabled:opacity-50"
                        >
                          📅 {t.apActExtract}
                        </button>
                        <button
                          onClick={() =>
                            setAction({
                              type: "draft", msgIdx: i, busy: false,
                              title: `${t.apActDraft} — ${ctxMatter?.reference || ""}`.trim(),
                            })
                          }
                          disabled={busy || Boolean(action?.busy)}
                          className="text-[11px] rounded-full border border-slate-200 px-2.5 py-1 text-slate-600 hover:border-indigo-300 hover:text-indigo-700 transition disabled:opacity-50"
                        >
                          📄 {t.apActDraft}
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Deadline proposals: the lawyer reviews before anything is saved */}
                {action?.type === "deadlines" && action.msgIdx === i && (
                  <div className="mt-1.5 rounded-xl border border-indigo-100 bg-indigo-50/60 p-3 space-y-2 text-xs">
                    {action.busy && !action.proposals && (
                      <p className="text-slate-500 animate-pulse">{t.thinking}</p>
                    )}
                    {action.proposals && action.proposals.length === 0 && (
                      <p className="text-slate-500">{t.apActNoDl}</p>
                    )}
                    {action.proposals?.map((p, j) => (
                      <label
                        key={j}
                        className={`flex items-start gap-2 ${p.due_date ? "cursor-pointer" : "opacity-50"}`}
                      >
                        <input
                          type="checkbox"
                          disabled={!p.due_date || action.busy}
                          checked={action.selected[j] && Boolean(p.due_date)}
                          onChange={(e) =>
                            setAction({
                              ...action,
                              selected: action.selected.map((s, k) => (k === j ? e.target.checked : s)),
                            })
                          }
                          className="accent-indigo-600 mt-0.5"
                        />
                        <span className="min-w-0">
                          <span className="font-medium text-slate-800">{p.title}</span>{" "}
                          {p.due_date ? <span className="text-indigo-700">— {p.due_date}</span> : null}
                          {p.legal_basis ? (
                            <span className="block text-slate-500">{p.legal_basis}</span>
                          ) : null}
                        </span>
                      </label>
                    ))}
                    <div className="flex items-center gap-2 pt-1">
                      {action.proposals && action.proposals.some((p, j) => action.selected[j] && p.due_date) && (
                        <Button
                          onClick={createSelectedDeadlines}
                          disabled={action.busy}
                          className="!px-3 !py-1.5 !text-xs"
                        >
                          {t.apActCreate.replace(
                            "{n}",
                            String(action.proposals.filter((p, j) => action.selected[j] && p.due_date).length)
                          )}
                        </Button>
                      )}
                      <button
                        onClick={() => setAction(null)}
                        disabled={action.busy}
                        className="text-slate-500 hover:text-slate-700 px-2 py-1.5"
                      >
                        {t.close}
                      </button>
                    </div>
                  </div>
                )}

                {/* Draft form: named by the lawyer, saved with ai_generated=true */}
                {action?.type === "draft" && action.msgIdx === i && (
                  <div className="mt-1.5 rounded-xl border border-indigo-100 bg-indigo-50/60 p-3 space-y-2 text-xs">
                    <label className="block">
                      <span className="text-slate-500">{t.apDraftTitle}</span>
                      <input
                        value={action.title}
                        onChange={(e) => setAction({ ...action, title: e.target.value })}
                        disabled={action.busy}
                        className="mt-1 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm bg-white"
                      />
                    </label>
                    <div className="flex items-center gap-2">
                      <Button
                        onClick={saveDraft}
                        disabled={action.busy || !action.title.trim()}
                        className="!px-3 !py-1.5 !text-xs"
                      >
                        {action.busy ? t.loading : t.apActDraft}
                      </Button>
                      <button
                        onClick={() => setAction(null)}
                        disabled={action.busy}
                        className="text-slate-500 hover:text-slate-700 px-2 py-1.5"
                      >
                        {t.close}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {notice && (
            <p className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              ✓ {notice}
              {ctxMatter && (
                <>
                  {" "}
                  <Link
                    href={`/matters/${ctxMatter.id}`}
                    onClick={() => setOpen(false)}
                    className="underline"
                  >
                    {ctxMatter.reference}
                  </Link>
                </>
              )}
            </p>
          )}
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
          {/* Ava Agent work plan (D-054): live step checklist */}
          {agentSteps.length > 0 && (
            <div className="text-xs bg-violet-50/70 border border-violet-100 rounded-xl px-3.5 py-2.5 space-y-1.5">
              <p className="font-semibold text-violet-700">🤖 {t.agPlanT}</p>
              {agentSteps.map((s, i) => (
                <p
                  key={i}
                  className={`flex items-start gap-1.5 ${
                    s.status === "running"
                      ? "text-violet-800 animate-pulse"
                      : s.status === "failed"
                        ? "text-rose-600"
                        : s.status === "done"
                          ? "text-slate-600"
                          : "text-slate-400"
                  }`}
                >
                  <span className="shrink-0">
                    {s.status === "done" ? "✓" : s.status === "running" ? "→" : s.status === "failed" ? "✕" : "○"}
                  </span>
                  <span>{s.label}</span>
                </p>
              ))}
            </div>
          )}
          {busy && agentMode && agentSteps.length === 0 && (
            <p className="text-sm text-slate-400 animate-pulse">{t.agPlanning}</p>
          )}
          {busy && !agentMode && steps.length === 0 && !messages.some((m) => m.id === "streaming") && (
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
