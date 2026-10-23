import type { MetadataRoute } from "next";
import type { Country } from "@/lib/country";
import { COUNTRY_BASE_URL, serverCountry } from "@/lib/seo";
import { RATGEBER_ARTICLES } from "@/lib/ratgeber";
import { UDHEZUES_ARTICLES } from "@/lib/udhezues";

// Public, indexable pages only (see robots.ts for what stays out). Served
// per host (D-039): the DE sitemap must list German pages on the DE domain,
// not Kosovo URLs. XK: null means the route is XK-only, DE likewise.
const ROUTES: { path: string; priority: number; only?: Country }[] = [
  { path: "/", priority: 1 },
  { path: "/per-qytetaret", priority: 0.9 },
  { path: "/per-avokatet", priority: 0.9 },
  { path: "/per-noteret", priority: 0.8, only: "XK" },
  { path: "/avokatet", priority: 0.9 },
  { path: "/noteret", priority: 0.8, only: "XK" },
  { path: "/ava", priority: 0.9 },
  { path: "/posto-rastin", priority: 0.8 },
  { path: "/afatet", priority: 0.7 },
  { path: "/rvg", priority: 0.7, only: "DE" },
  { path: "/ratgeber", priority: 0.7, only: "DE" },
  { path: "/udhezues", priority: 0.7, only: "XK" },
  { path: "/kostoja", priority: 0.7, only: "XK" },
  { path: "/dokumentet", priority: 0.7 },
  { path: "/regjistrohu", priority: 0.6 },
  { path: "/kontakti", priority: 0.5 },
  { path: "/siguria", priority: 0.4 },
  { path: "/impressum", priority: 0.3, only: "DE" },
  { path: "/kushtet", priority: 0.3 },
  { path: "/privatesia", priority: 0.3 },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const country = await serverCountry();
  const base = COUNTRY_BASE_URL[country];
  const lastModified = new Date();
  const entries: MetadataRoute.Sitemap = ROUTES.filter(
    (r) => !r.only || r.only === country
  ).map(({ path, priority }) => ({
    url: `${base}${path}`,
    lastModified,
    changeFrequency: path === "/avokatet" || path === "/noteret" ? "daily" : "weekly",
    priority,
  }));

  // Guide articles are per-country content: German Ratgeber on the DE host
  // (D-045), Albanian udhëzues on the XK host (D-048).
  if (country === "DE") {
    for (const a of RATGEBER_ARTICLES) {
      entries.push({
        url: `${base}/ratgeber/${a.slug}`,
        lastModified: new Date(a.updated),
        changeFrequency: "monthly",
        priority: 0.6,
      });
    }
  } else {
    for (const a of UDHEZUES_ARTICLES) {
      entries.push({
        url: `${base}/udhezues/${a.slug}`,
        lastModified: new Date(a.updated),
        changeFrequency: "monthly",
        priority: 0.6,
      });
    }
  }

  // Every lawyer profile is its own citable URL (GEO/SEO), scoped to the
  // host's country so the DE sitemap never lists Kosovo profiles.
  try {
    const res = await fetch("http://127.0.0.1:8000/api/public/lawyers", {
      headers: { "x-avokatim-country": country },
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const lawyers: { id: string }[] = await res.json();
      for (const l of lawyers) {
        entries.push({
          url: `${base}/avokatet/${l.id}`,
          lastModified,
          changeFrequency: "weekly",
          priority: 0.7,
        });
      }
    }
  } catch {
    // Backend unavailable at build time: static routes are still served
  }
  return entries;
}
