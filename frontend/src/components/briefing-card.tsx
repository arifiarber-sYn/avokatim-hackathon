"use client";

/** Morning briefing card (D-054 F3): today's LLM-generated day summary on
 * the dashboard, with local TTS ("listen to your day") and dismiss. */
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { SpeakButton, useVoiceAvailable } from "@/components/voice-controls";

interface BriefingItem {
  id: string;
  title: string;
  body: string | null;
  read_at: string | null;
  created_at: string;
}

export function BriefingCard() {
  const { t, locale } = useI18n();
  const voice = useVoiceAvailable();
  const [briefing, setBriefing] = useState<BriefingItem | null>(null);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    apiGet<BriefingItem[]>("/notifications?kind=briefing&limit=1")
      .then((rows) => {
        const b = rows[0];
        if (!b || !b.body) return;
        const isToday =
          new Date(b.created_at).toDateString() === new Date().toDateString();
        if (isToday) setBriefing(b);
      })
      .catch(() => {});
  }, []);

  if (!briefing || hidden) return null;

  function dismiss() {
    setHidden(true);
    apiPost(`/notifications/${briefing!.id}/read`).catch(() => {});
  }

  return (
    <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-violet-50/60 p-4 md:p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-bold text-indigo-800">{briefing.title}</p>
        <div className="flex items-center gap-1 shrink-0">
          {briefing.body && (
            <SpeakButton text={briefing.body} locale={locale} serverTts={voice.tts} />
          )}
          <button
            onClick={dismiss}
            aria-label={t.close}
            className="h-7 w-7 rounded-full hover:bg-indigo-100 text-slate-400 hover:text-slate-600 flex items-center justify-center leading-none"
          >
            ×
          </button>
        </div>
      </div>
      <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
        {briefing.body}
      </p>
    </div>
  );
}
