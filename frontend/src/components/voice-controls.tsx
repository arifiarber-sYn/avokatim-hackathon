"use client";

// Reusable voice controls (Faza 3): a push-to-talk mic that fills a text
// callback, and a speak button that reads a message out loud.
import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/lib/i18n";
import {
  pickRecorderMime,
  speak,
  stopSpeaking,
  transcribeBlob,
  voiceStatus,
} from "@/lib/voice";

export function useVoiceAvailable(): { stt: boolean; tts: boolean } {
  const [status, setStatus] = useState({ stt: false, tts: false });
  useEffect(() => {
    voiceStatus().then(setStatus);
  }, []);
  return status;
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0M12 17v4" strokeLinecap="round" />
    </svg>
  );
}

/** Hold-to-talk microphone; transcribes locally and calls onText. */
export function MicButton({
  locale,
  onText,
  disabled,
}: {
  locale: string;
  onText: (text: string) => void;
  disabled?: boolean;
}) {
  const { t } = useI18n();
  const [state, setState] = useState<"idle" | "recording" | "busy">("idle");
  const [error, setError] = useState("");
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    return () => streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  async function start() {
    if (state !== "idle" || disabled) return;
    setError("");
    try {
      if (!streamRef.current?.active) {
        streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      const rec = new MediaRecorder(streamRef.current, { mimeType: pickRecorderMime() });
      recRef.current = rec;
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = () => void finish();
      rec.start();
      setState("recording");
    } catch {
      setError(t.sosMicDenied);
    }
  }

  function stop() {
    if (recRef.current?.state === "recording") recRef.current.stop();
  }

  async function finish() {
    setState("busy");
    try {
      const blob = new Blob(chunksRef.current, { type: pickRecorderMime() });
      if (blob.size > 1000) {
        const result = await transcribeBlob(blob, locale);
        if (result.text.trim()) onText(result.text.trim());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setState("idle");
    }
  }

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        title={t.vMicHint}
        onPointerDown={(e) => {
          e.preventDefault();
          void start();
        }}
        onPointerUp={stop}
        onPointerLeave={stop}
        onContextMenu={(e) => e.preventDefault()}
        disabled={disabled || state === "busy"}
        className={`h-10 w-10 rounded-lg flex items-center justify-center select-none touch-none border transition ${
          state === "recording"
            ? "bg-red-600 border-red-600 text-white animate-pulse"
            : state === "busy"
              ? "bg-slate-100 border-slate-200 text-slate-400"
              : "bg-white border-slate-300 text-slate-600 hover:text-indigo-600 hover:border-indigo-300"
        }`}
        aria-label={t.vMic}
      >
        <MicIcon className="h-5 w-5" />
      </button>
      {error && (
        <span className="absolute bottom-full mb-1 right-0 text-[11px] text-red-600 bg-white border border-red-200 rounded px-2 py-1 whitespace-nowrap shadow-sm">
          {error}
        </span>
      )}
    </span>
  );
}

/** Reads a message out loud (Piper for sq, browser voices otherwise). */
export function SpeakButton({
  text,
  locale,
  serverTts,
}: {
  text: string;
  locale: string;
  serverTts: boolean;
}) {
  const { t } = useI18n();
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => () => stopSpeaking(), []);

  async function toggle() {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    setSpeaking(true);
    await speak(text, locale, serverTts);
    setSpeaking(false);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      className={`inline-flex items-center gap-1 text-[11px] rounded-full px-2 py-0.5 transition ${
        speaking
          ? "bg-indigo-600 text-white"
          : "bg-slate-100 text-slate-500 hover:text-indigo-600"
      }`}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-3 w-3">
        <path d="M11 5 6 9H2v6h4l5 4V5zM15.5 8.5a5 5 0 0 1 0 7M19 5a9 9 0 0 1 0 14" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {speaking ? t.vStopAudio : t.vPlay}
    </button>
  );
}
