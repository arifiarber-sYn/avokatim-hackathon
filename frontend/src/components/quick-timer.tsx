"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Label, Select, Textarea } from "@/components/ui";

const TIMER_KEY = "avokatim_timer_start";

interface MatterOption {
  id: string;
  reference: string;
  title: string;
  status: string;
}

function formatElapsed(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

export function QuickTimer() {
  const { t } = useI18n();
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [showSave, setShowSave] = useState(false);
  const [matters, setMatters] = useState<MatterOption[]>([]);
  const [matterId, setMatterId] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(TIMER_KEY);
    if (saved) setStartedAt(Number(saved));
  }, []);

  useEffect(() => {
    if (startedAt === null) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  const start = () => {
    const ts = Date.now();
    localStorage.setItem(TIMER_KEY, String(ts));
    setStartedAt(ts);
  };

  const openSave = () => {
    setShowSave(true);
    apiGet<MatterOption[]>("/matters")
      .then((list) => {
        const open = list.filter((m) => m.status === "open" || m.status === "intake");
        setMatters(open);
        if (open.length > 0) setMatterId(open[0].id);
      })
      .catch(() => {});
  };

  const reset = () => {
    localStorage.removeItem(TIMER_KEY);
    setStartedAt(null);
    setShowSave(false);
    setDescription("");
    setBusy(false);
  };

  const save = async () => {
    if (!startedAt || !matterId || !description.trim()) return;
    setBusy(true);
    try {
      await apiPost("/time-entries", {
        matter_id: matterId,
        started_at: new Date(startedAt).toISOString(),
        minutes: Math.max(1, Math.round((Date.now() - startedAt) / 60000)),
        description: description.trim(),
        billable: true,
      });
      reset();
    } catch {
      setBusy(false);
    }
  };

  if (startedAt === null) {
    return (
      <button
        onClick={start}
        className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
      >
        <span>▶</span> {t.startTimer}
      </button>
    );
  }

  return (
    <>
      <button
        onClick={openSave}
        className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-600/20 text-red-300 hover:bg-red-600/30 transition-colors"
        title={t.stopTimer}
      >
        <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
        {t.timerRunning} · <span className="tabular-nums">{formatElapsed(now - startedAt)}</span>
      </button>

      {showSave && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-5 space-y-4 text-slate-900">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{t.saveTimeEntry}</h3>
              <span className="text-lg font-bold tabular-nums text-indigo-600">
                {formatElapsed(now - startedAt)}
              </span>
            </div>
            <div>
              <Label>{t.selectMatter}</Label>
              <Select value={matterId} onChange={(e) => setMatterId(e.target.value)}>
                {matters.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.reference} — {m.title}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t.whatDidYouWorkOn}</Label>
              <Textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                autoFocus
              />
            </div>
            <div className="flex items-center justify-between">
              <Button variant="ghost" onClick={reset}>
                {t.discardTimer}
              </Button>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => setShowSave(false)}>
                  {t.cancel}
                </Button>
                <Button onClick={save} disabled={busy || !matterId || !description.trim()}>
                  {t.saveTimeEntry}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
