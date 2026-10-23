"use client";

// Global browser-error relay (D-054 F6): uncaught errors and unhandled
// promise rejections go to /api/public/client-error, which forwards them to
// the self-hosted GlitchTip. Deduped and capped so a render loop can't
// flood the backend. No PII — message, stack and URL only.
import { useEffect } from "react";

const MAX_PER_SESSION = 5;
let sent = 0;
const seen = new Set<string>();

function report(message: string, stack?: string) {
  if (sent >= MAX_PER_SESSION) return;
  const key = message.slice(0, 200);
  if (seen.has(key)) return;
  seen.add(key);
  sent += 1;
  const body = JSON.stringify({
    message: message.slice(0, 2000),
    stack: stack?.slice(0, 8000),
    url: window.location.pathname,
  });
  // sendBeacon survives page unloads; fall back to fetch
  try {
    if (!navigator.sendBeacon?.(
      "/api/public/client-error",
      new Blob([body], { type: "application/json" })
    )) {
      void fetch("/api/public/client-error", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(() => {});
    }
  } catch {}
}

export default function ErrorReporter() {
  useEffect(() => {
    const onError = (e: ErrorEvent) => {
      // Ignore noise from browser extensions / cross-origin scripts
      if (!e.message || e.message === "Script error.") return;
      report(e.message, e.error instanceof Error ? e.error.stack : undefined);
    };
    const onRejection = (e: PromiseRejectionEvent) => {
      const reason = e.reason;
      if (reason instanceof Error) report(`Unhandled rejection: ${reason.message}`, reason.stack);
      else if (typeof reason === "string") report(`Unhandled rejection: ${reason}`);
    };
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);
  return null;
}
