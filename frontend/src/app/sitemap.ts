import type { MetadataRoute } from "next";

const BASE = "https://avokatiim.ai";

// Public, indexable pages only (see robots.ts for what stays out).
const ROUTES: { path: string; priority: number }[] = [
  { path: "/", priority: 1 },
  { path: "/per-qytetaret", priority: 0.9 },
  { path: "/per-avokatet", priority: 0.9 },
  { path: "/per-noteret", priority: 0.8 },
  { path: "/avokatet", priority: 0.9 },
  { path: "/noteret", priority: 0.8 },
  { path: "/ava", priority: 0.9 },
  { path: "/posto-rastin", priority: 0.8 },
  { path: "/afatet", priority: 0.7 },
  { path: "/dokumentet", priority: 0.7 },
  { path: "/apliko", priority: 0.6 },
  { path: "/regjistrohu", priority: 0.6 },
  { path: "/kontakti", priority: 0.5 },
  { path: "/siguria", priority: 0.4 },
  { path: "/kushtet", priority: 0.3 },
  { path: "/privatesia", priority: 0.3 },
];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return ROUTES.map(({ path, priority }) => ({
    url: `${BASE}${path}`,
    lastModified,
    changeFrequency: path === "/avokatet" || path === "/noteret" ? "daily" : "weekly",
    priority,
  }));
}
