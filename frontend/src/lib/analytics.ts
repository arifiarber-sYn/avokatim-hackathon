// Product events for the self-hosted Umami (D-054 F6): feature usage, not
// just pageviews. No-op when the analytics script isn't loaded (dev, or
// NEXT_PUBLIC_UMAMI_* unset). Event names are stable, snake_case, and carry
// no PII — counts only.
declare global {
  interface Window {
    umami?: { track: (event: string, data?: Record<string, string | number>) => void };
  }
}

export function track(event: string, data?: Record<string, string | number>) {
  try {
    window.umami?.track(event, data);
  } catch {}
}
