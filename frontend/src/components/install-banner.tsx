"use client";

/** PWA install banner (D-054 F5): shown only after real engagement
 * (2nd visit or later), never on the first impression, and snoozed for
 * 30 days on dismiss. Uses beforeinstallprompt where available. */
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { haptic } from "@/lib/haptics";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const VISITS_KEY = "avokatim-visits";
const SNOOZE_KEY = "avokatim-install-snooze";

export function InstallBanner() {
  const { t } = useI18n();
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const standalone = window.matchMedia("(display-mode: standalone)").matches;
      if (standalone) return;
      const snooze = Number(localStorage.getItem(SNOOZE_KEY) || 0);
      if (snooze > Date.now()) return;
      const visits = Number(localStorage.getItem(VISITS_KEY) || 0) + 1;
      localStorage.setItem(VISITS_KEY, String(visits));
      if (visits < 2) return;
    } catch {
      return;
    }

    const onPrompt = (e: Event) => {
      e.preventDefault();
      setPromptEvent(e as BeforeInstallPromptEvent);
      setVisible(true);
    };
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

  if (!visible || !promptEvent) return null;

  async function install() {
    haptic();
    try {
      await promptEvent!.prompt();
      await promptEvent!.userChoice;
    } finally {
      setVisible(false);
    }
  }

  function later() {
    try {
      localStorage.setItem(SNOOZE_KEY, String(Date.now() + 30 * 86_400_000));
    } catch {
      /* private mode */
    }
    setVisible(false);
  }

  return (
    <div
      className="fixed inset-x-3 bottom-20 md:bottom-6 md:left-auto md:right-6 md:w-96 z-40 rounded-2xl bg-slate-900 text-white shadow-2xl p-4 flex items-start gap-3"
      style={{ marginBottom: "env(safe-area-inset-bottom)" }}
      role="dialog"
      aria-label={t.pwaInstallT}
    >
      <span className="h-10 w-10 rounded-xl bg-indigo-500/25 text-indigo-300 flex items-center justify-center text-lg shrink-0">
        ⬇
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold">{t.pwaInstallT}</p>
        <p className="text-xs text-slate-300 mt-0.5">{t.pwaInstallB}</p>
        <div className="mt-2.5 flex gap-2">
          <button
            onClick={install}
            className="rounded-lg bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-semibold px-3.5 py-1.5 transition"
          >
            {t.pwaInstallBtn}
          </button>
          <button
            onClick={later}
            className="rounded-lg text-slate-300 hover:text-white text-xs px-2.5 py-1.5"
          >
            {t.pwaLater}
          </button>
        </div>
      </div>
    </div>
  );
}
