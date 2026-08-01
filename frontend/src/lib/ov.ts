// Zivilgerichtliches Online-Verfahren (D-041) — citizen-side matcher.
// Information only (RDG-safe): we never advise, we point to the official
// portal when the case looks like something the citizen could file there:
// a flight-rights claim or a payment claim mentioning an amount <= 10,000 €.

const OV_FLIGHT = /flug|flight|airline|annullier|versp[äa]t|fluggast/i;

export function ovCaseMatch(text: string): boolean {
  if (text.trim().length < 20) return false;
  if (OV_FLIGHT.test(text)) return true;
  for (const m of text.matchAll(/(\d[\d.,]{0,9})\s*(?:€|euro)/gi)) {
    const n = Number(m[1].replace(/\./g, "").replace(",", "."));
    if (n > 0 && n <= 10000) return true;
  }
  return false;
}

export const OV_PORTAL_URL = "https://service.justiz.de/klagen-ohne-anwalt";
