"use client";

// SOS screen (D-018 "AI protection by phone"): three big actions —
// record evidence, talk to Ava by voice, alert on-duty lawyers.
// Evidence audio streams to the encrypted vault in 5-second chunks while
// recording (ACLU Mobile Justice model: survives phone seizure). The same
// microphone serves push-to-talk with Ava through a second MediaRecorder.
import { useCallback, useEffect, useRef, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { citizenPost, citizenUpload } from "@/lib/citizen";
import {
  pickRecorderMime,
  speak,
  stopSpeaking,
  transcribeBlob,
  voiceStatus,
  VoiceStatus,
} from "@/lib/voice";
import { Button, Card, ErrorNote, Input, Label, Textarea } from "@/components/ui";

const CONSENT_KEY = "avokatim:sos:consent";

interface AvaTurn {
  role: "user" | "assistant";
  content: string;
}

export default function SosPanel({
  locale,
  onCaseCreated,
}: {
  locale: string;
  onCaseCreated: () => void;
}) {
  const { t } = useI18n();
  const [consent, setConsent] = useState<boolean | null>(null);
  const [voice, setVoice] = useState<VoiceStatus>({ stt: false, tts: false });
  const [error, setError] = useState("");

  // --- evidence recording state
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [savedChunks, setSavedChunks] = useState(0);
  const [savedNote, setSavedNote] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const evidenceRecRef = useRef<MediaRecorder | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const seqRef = useRef(0);
  const uploadChainRef = useRef<Promise<void>>(Promise.resolve());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // --- push-to-talk / Ava state
  const [ptt, setPtt] = useState<"idle" | "recording" | "transcribing" | "thinking" | "speaking">("idle");
  const [turns, setTurns] = useState<AvaTurn[]>([]);
  const pttRecRef = useRef<MediaRecorder | null>(null);
  const pttChunksRef = useRef<Blob[]>([]);

  // --- SOS dispatch state
  const [dispatchOpen, setDispatchOpen] = useState(false);
  const [sos, setSos] = useState({ description: "", city: "" });
  const [sosBusy, setSosBusy] = useState(false);
  const [sosSent, setSosSent] = useState(false);
  const caseIdRef = useRef<string | null>(null);

  useEffect(() => {
    try {
      setConsent(localStorage.getItem(CONSENT_KEY) === "1");
    } catch {
      setConsent(false);
    }
    voiceStatus().then(setVoice);
    return () => {
      stopSpeaking();
      evidenceRecRef.current?.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  function acceptConsent() {
    try {
      localStorage.setItem(CONSENT_KEY, "1");
    } catch {}
    setConsent(true);
  }

  const getMic = useCallback(async (): Promise<MediaStream> => {
    if (streamRef.current?.active) return streamRef.current;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    return stream;
  }, []);

  // ---------- evidence recording ----------

  async function startEvidence() {
    setError("");
    try {
      const stream = await getMic();
      const mime = pickRecorderMime();
      const session = await citizenPost<{ id: string }>("/citizen/evidence/start", {
        kind: "sos_audio",
        mime,
        consent: true,
        case_request_id: caseIdRef.current,
      });
      sessionIdRef.current = session.id;
      seqRef.current = 0;
      setSavedChunks(0);
      setSavedNote(false);

      const rec = new MediaRecorder(stream, { mimeType: mime });
      evidenceRecRef.current = rec;
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) queueChunk(e.data);
      };
      rec.start(5000);
      setRecording(true);
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    } catch (err) {
      setError(
        err instanceof Error && err.name === "NotAllowedError"
          ? t.sosMicDenied
          : err instanceof Error
            ? err.message
            : t.error
      );
    }
  }

  function queueChunk(blob: Blob) {
    const sessionId = sessionIdRef.current;
    if (!sessionId) return;
    const seq = seqRef.current++;
    // Chunks must arrive in order (hash chain) — serialize uploads
    uploadChainRef.current = uploadChainRef.current.then(async () => {
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const form = new FormData();
          form.append("seq", String(seq));
          form.append("chunk", blob, `chunk-${seq}.webm`);
          await citizenUpload(`/citizen/evidence/${sessionId}/chunks`, form);
          setSavedChunks((n) => n + 1);
          return;
        } catch {
          await new Promise((r) => setTimeout(r, 1500 * (attempt + 1)));
        }
      }
    });
  }

  async function stopEvidence() {
    const rec = evidenceRecRef.current;
    if (rec && rec.state !== "inactive") rec.stop();
    setRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    // Let the final ondataavailable fire, then flush the queue and finish
    setTimeout(async () => {
      await uploadChainRef.current;
      const sessionId = sessionIdRef.current;
      if (sessionId) {
        try {
          await citizenPost(`/citizen/evidence/${sessionId}/finish`, {
            case_request_id: caseIdRef.current,
          });
          setSavedNote(true);
        } catch {}
      }
    }, 400);
  }

  // ---------- push-to-talk with Ava ----------

  async function pttStart() {
    if (ptt !== "idle" || !voice.stt) return;
    setError("");
    stopSpeaking();
    try {
      const stream = await getMic();
      const rec = new MediaRecorder(stream, { mimeType: pickRecorderMime() });
      pttRecRef.current = rec;
      pttChunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) pttChunksRef.current.push(e.data);
      };
      rec.onstop = () => void pttFinished();
      rec.start();
      setPtt("recording");
    } catch (err) {
      setError(
        err instanceof Error && err.name === "NotAllowedError" ? t.sosMicDenied : t.error
      );
    }
  }

  function pttStop() {
    const rec = pttRecRef.current;
    if (rec && rec.state === "recording") rec.stop();
  }

  async function pttFinished() {
    setPtt("transcribing");
    try {
      const blob = new Blob(pttChunksRef.current, { type: pickRecorderMime() });
      if (blob.size < 1000) {
        setPtt("idle");
        return;
      }
      const heard = await transcribeBlob(blob, locale);
      if (!heard.text.trim()) {
        setPtt("idle");
        return;
      }
      const question = heard.text.trim();
      const history = turns.slice(-8);
      setTurns((prev) => [...prev, { role: "user", content: question }]);
      setPtt("thinking");
      const reply = await citizenPost<{ answer: string }>("/ava/ask", {
        question,
        history,
      });
      setTurns((prev) => [...prev, { role: "assistant", content: reply.answer }]);
      setPtt("speaking");
      await speak(reply.answer, locale, voice.tts);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setPtt("idle");
    }
  }

  // ---------- SOS dispatch ----------

  function openDispatch() {
    const transcript = turns
      .filter((turn) => turn.role === "user")
      .map((turn) => turn.content)
      .join(" ");
    setSos((s) => ({ ...s, description: s.description || transcript }));
    setDispatchOpen(true);
  }

  async function sendSos(e: React.FormEvent) {
    e.preventDefault();
    setSosBusy(true);
    setError("");
    try {
      const created = await citizenPost<{ id: string }>("/citizen/sos", {
        description: sos.description.trim(),
        city: sos.city.trim() || null,
        evidence_session_id: sessionIdRef.current,
      });
      caseIdRef.current = created.id;
      setSosSent(true);
      setDispatchOpen(false);
      onCaseCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setSosBusy(false);
    }
  }

  const mmss = `${String(Math.floor(elapsed / 60)).padStart(2, "0")}:${String(elapsed % 60).padStart(2, "0")}`;

  if (consent === null) return null;

  if (!consent) {
    return (
      <Card className="p-5 space-y-3 border-red-200">
        <h2 className="font-bold text-red-700">{t.sosConsentT}</h2>
        <p className="text-sm text-slate-600 leading-relaxed">{t.sosConsentBody}</p>
        <div className="flex gap-2">
          <Button onClick={acceptConsent} className="!bg-red-600 hover:!bg-red-700">
            {t.sosConsentAgree}
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5 space-y-4 border-red-200">
      <div>
        <h2 className="font-bold text-red-700">{t.sosTitle}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.sosSubtitle}</p>
      </div>
      <ErrorNote message={error} />

      {/* action 1: record evidence */}
      {!recording ? (
        <button
          onClick={startEvidence}
          className="w-full rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold py-4 text-base shadow-sm"
        >
          ⏺ {t.sosRecordBtn}
          <span className="block text-[11px] font-normal opacity-80 mt-0.5">
            {t.sosRecordHint}
          </span>
        </button>
      ) : (
        <div className="rounded-xl border border-red-300 bg-red-50 p-4 space-y-2">
          <p className="text-sm font-bold text-red-700 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-600" />
            </span>
            {t.sosRecordingLive}
          </p>
          <p className="text-xs text-red-800 font-mono">
            {mmss} · {savedChunks} {t.evChunksWord} ✓
          </p>
          <Button onClick={stopEvidence} variant="secondary" className="w-full">
            {t.sosStopBtn}
          </Button>
        </div>
      )}
      {savedNote && !recording && (
        <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
          {t.sosSavedOk}
        </p>
      )}

      {/* action 2: talk to Ava (push-to-talk) */}
      {voice.stt ? (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-4 space-y-3">
          <p className="text-sm font-bold text-indigo-800">
            🎙 {t.sosTalkBtn}
            <span className="block text-[11px] font-normal text-indigo-600 mt-0.5">
              {t.sosTalkHint}
            </span>
          </p>
          {turns.length > 0 && (
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {turns.slice(-4).map((turn, i) => (
                <p
                  key={i}
                  className={`text-sm rounded-lg px-3 py-1.5 ${
                    turn.role === "user"
                      ? "bg-white text-slate-700 border border-slate-200"
                      : "bg-indigo-600 text-white"
                  }`}
                >
                  {turn.content}
                </p>
              ))}
            </div>
          )}
          <button
            onPointerDown={(e) => {
              e.preventDefault();
              void pttStart();
            }}
            onPointerUp={pttStop}
            onPointerLeave={pttStop}
            onContextMenu={(e) => e.preventDefault()}
            disabled={ptt !== "idle" && ptt !== "recording"}
            className={`w-full rounded-xl font-bold py-4 text-white select-none touch-none transition ${
              ptt === "recording"
                ? "bg-indigo-800 scale-[0.99]"
                : ptt === "idle"
                  ? "bg-indigo-600 hover:bg-indigo-700"
                  : "bg-indigo-400"
            }`}
          >
            {ptt === "recording"
              ? "● " + t.sosHoldToTalk
              : ptt === "transcribing"
                ? t.sosTranscribing
                : ptt === "thinking"
                  ? t.avaThinkingV
                  : ptt === "speaking"
                    ? t.avaSpeakingV
                    : t.sosHoldToTalk}
          </button>
          {ptt === "speaking" && (
            <button
              onClick={() => {
                stopSpeaking();
                setPtt("idle");
              }}
              className="text-xs text-indigo-600 hover:underline"
            >
              {t.vStopAudio}
            </button>
          )}
        </div>
      ) : null}

      {/* action 3: alert on-duty lawyers */}
      {sosSent ? (
        <p className="text-sm bg-red-50 text-red-700 rounded-lg p-3">{t.mkSosSent}</p>
      ) : !dispatchOpen ? (
        <button
          onClick={openDispatch}
          className="w-full rounded-xl border-2 border-red-600 text-red-700 hover:bg-red-50 font-bold py-4"
        >
          🚨 {t.sosCallBtn}
          <span className="block text-[11px] font-normal mt-0.5">{t.sosCallHint}</span>
        </button>
      ) : (
        <form onSubmit={sendSos} className="rounded-xl border border-red-200 p-4 space-y-3">
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
            <Input value={sos.city} onChange={(e) => setSos({ ...sos, city: e.target.value })} />
          </div>
          <Button type="submit" disabled={sosBusy} className="w-full !bg-red-600 hover:!bg-red-700">
            {sosBusy ? t.loading : t.mkSosSend}
          </Button>
        </form>
      )}
    </Card>
  );
}
