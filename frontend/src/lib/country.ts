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

/** German Bundesländer (ISO 3166-2 codes without "DE-") — mirrors the
    `regions` map of the DE profile in backend/app/jurisdictions.py. The
    office's Land selects the regional holiday calendar for deadlines. */
export const DE_REGIONS: { code: string; name: string }[] = [
  { code: "BW", name: "Baden-Württemberg" },
  { code: "BY", name: "Bayern" },
  { code: "BE", name: "Berlin" },
  { code: "BB", name: "Brandenburg" },
  { code: "HB", name: "Bremen" },
  { code: "HH", name: "Hamburg" },
  { code: "HE", name: "Hessen" },
  { code: "MV", name: "Mecklenburg-Vorpommern" },
  { code: "NI", name: "Niedersachsen" },
  { code: "NW", name: "Nordrhein-Westfalen" },
  { code: "RP", name: "Rheinland-Pfalz" },
  { code: "SL", name: "Saarland" },
  { code: "SN", name: "Sachsen" },
  { code: "ST", name: "Sachsen-Anhalt" },
  { code: "SH", name: "Schleswig-Holstein" },
  { code: "TH", name: "Thüringen" },
];

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
