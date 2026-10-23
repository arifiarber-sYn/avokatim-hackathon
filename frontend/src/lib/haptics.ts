/** Tiny haptic feedback for key mobile actions (D-054 F5). No-ops where
 * the Vibration API is unavailable (iOS Safari, desktop). */
export function haptic(pattern: number | number[] = 10) {
  try {
    if (typeof navigator !== "undefined" && "vibrate" in navigator) {
      navigator.vibrate(pattern);
    }
  } catch {
    /* never break a tap over feedback */
  }
}
