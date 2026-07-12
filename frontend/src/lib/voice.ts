// Voice helpers: local STT/TTS via the backend (Albanian) with the
// browser's speechSynthesis as fallback for the other locales.
import { getCitizenToken } from "./citizen";

export interface VoiceStatus {
  stt: boolean;
  tts: boolean;
}

export async function voiceStatus(): Promise<VoiceStatus> {
  try {
    const res = await fetch("/api/public/voice/status");
    if (!res.ok) return { stt: false, tts: false };
    return await res.json();
  } catch {
    return { stt: false, tts: false };
  }
}

function authHeaders(): Record<string, string> {
  const token = getCitizenToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface TranscriptResult {
  text: string;
  language: string;
  duration: number;
}

export async function transcribeBlob(
  blob: Blob,
  language?: string
): Promise<TranscriptResult> {
  const form = new FormData();
  form.append("audio", blob, "audio.webm");
  if (language) form.append("language", language);
  const res = await fetch("/api/public/voice/transcribe", {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

let currentAudio: HTMLAudioElement | null = null;

export function stopSpeaking() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

/** Speak text out loud: Piper (server, Albanian) or browser voices. */
export async function speak(
  text: string,
  locale: string,
  serverTts: boolean
): Promise<void> {
  stopSpeaking();
  const clean = text.replace(/\*\*?|__|##+|\[.*?\]\(.*?\)/g, "").slice(0, 900);
  if (locale === "sq" && serverTts) {
    const res = await fetch("/api/public/voice/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ text: clean }),
    });
    if (res.ok) {
      const url = URL.createObjectURL(await res.blob());
      await new Promise<void>((resolve) => {
        const audio = new Audio(url);
        currentAudio = audio;
        audio.onended = audio.onerror = () => {
          URL.revokeObjectURL(url);
          if (currentAudio === audio) currentAudio = null;
          resolve();
        };
        audio.play().catch(() => resolve());
      });
      return;
    }
  }
  // Browser fallback (sr/tr/bs/en/zh have built-in voices on most devices)
  if (typeof window !== "undefined" && window.speechSynthesis) {
    await new Promise<void>((resolve) => {
      const utter = new SpeechSynthesisUtterance(clean);
      utter.lang = { sq: "sq-AL", sr: "sr-RS", tr: "tr-TR", bs: "bs-BA", en: "en-US", zh: "zh-CN" }[locale] || locale;
      utter.onend = () => resolve();
      utter.onerror = () => resolve();
      window.speechSynthesis.speak(utter);
    });
  }
}

/** Preferred MediaRecorder mime for this browser. */
export function pickRecorderMime(): string {
  if (typeof MediaRecorder === "undefined") return "audio/webm";
  for (const mime of ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"]) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return "audio/webm";
}
