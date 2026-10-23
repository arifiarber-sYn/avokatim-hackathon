// Server-side country resolution for per-host SEO (D-034/D-039).
// The proxy sets x-avokatim-country from the Host header; server components
// and generateMetadata read it here. Using headers() opts the route into
// dynamic rendering — acceptable: the app is served by Next itself.
import { headers } from "next/headers";
import type { Country } from "./country";

export async function serverCountry(): Promise<Country> {
  const c = (await headers()).get("x-avokatim-country");
  return c === "DE" ? "DE" : "XK";
}

export const COUNTRY_BASE_URL: Record<Country, string> = {
  XK: "https://avokatiim.ai",
  DE: "https://de.avokatiim.ai",
};

// DE rebrand (D-056): the German host trades under "Ava Legal"; Kosovo
// keeps "AvokatIM". Client components get the same via lib/i18n's rebrand.
export const COUNTRY_BRAND: Record<Country, string> = {
  XK: "AvokatIM",
  DE: "Ava Legal",
};
