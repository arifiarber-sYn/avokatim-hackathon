"use client";

/**
 * Floating Ava launcher (D-052): the Intercom-style bottom-right entry point
 * that makes the AI assistant reachable from every public page — the pattern
 * ~90% of chat launchers follow and the one users expect on mobile.
 *
 * - Mobile: full-screen sheet (bottom nav is z-40; the sheet is z-50).
 * - Desktop: a 420px bottom-right panel so the page stays readable behind it.
 * - Hidden on /ava (there the chat IS the page) and while the panel is open.
 */
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import AvaChat from "@/components/ava-chat";
import { haptic } from "@/lib/haptics";
import { IconChat } from "@/components/icons";

export default function AvaLauncher() {
  const { t } = useI18n();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Escape closes the panel (desktop keyboard users)
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  // In-page CTAs (e.g. the /rasti-im card) open the sheet via this event (D-053)
  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener("avokatim:open-ava", onOpen);
    return () => window.removeEventListener("avokatim:open-ava", onOpen);
  }, []);

  if (pathname.startsWith("/ava")) return null;

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
          <span className="text-sm font-bold">{t.avaFabLabel}</span>
          <span className="text-[10px] font-semibold bg-white/20 rounded-full px-1.5 py-0.5">AI</span>
        </button>
      )}

      {open && (
        <div
          className="fixed inset-0 z-50 md:inset-auto md:right-4 md:bottom-4 md:w-[420px] md:h-[min(680px,calc(100vh-3rem))] bg-white md:rounded-2xl md:shadow-2xl md:ring-1 md:ring-slate-200 flex flex-col overflow-hidden"
          role="dialog"
          aria-label={t.mkAvaTitle}
        >
          <div className="flex items-center justify-between gap-3 px-4 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white shrink-0">
            <div className="flex items-center gap-2.5 min-w-0">
              <span className="h-8 w-8 rounded-full bg-white/15 flex items-center justify-center shrink-0">
                <IconChat className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="text-sm font-bold truncate">{t.mkAvaTitle}</p>
                <p className="text-[11px] text-indigo-100 truncate">{t.mkAvaIntro}</p>
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
          <div
            className="flex-1 overflow-y-auto px-4 py-3 flex flex-col"
            style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
          >
            <AvaChat variant="panel" />
          </div>
        </div>
      )}
    </>
  );
}
