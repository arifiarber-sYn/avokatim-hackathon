// Country scoping (D-034): which country's product a host serves.
// Mirrors backend/app/jurisdictions.py — keep the two in sync.

export type Country = "XK" | "DE";

export function countryForHost(host: string | null | undefined): Country {
  return (host || "").split(":")[0].toLowerCase() === "de.avokatiim.ai" ? "DE" : "XK";
}

/** Country of the current browser tab (XK during SSR — server components
    should read the x-avokatim-country header instead). */
export function clientCountry(): Country {
  if (typeof window === "undefined") return "XK";
  return countryForHost(window.location.hostname);
}

/** Per-country UX hints for forms (phone prefix, city suggestions). */
export const COUNTRY_UX: Record<Country, { phonePrefix: string; cities: string[] }> = {
  XK: {
    phonePrefix: "+383",
    cities: [
      "Prishtinë", "Prizren", "Pejë", "Gjakovë", "Mitrovicë",
      "Ferizaj", "Gjilan", "Vushtrri", "Podujevë", "Suharekë",
    ],
  },
  DE: {
    phonePrefix: "+49",
    cities: [
      "Berlin", "Hamburg", "München", "Köln", "Frankfurt am Main",
      "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen",
    ],
  },
};
