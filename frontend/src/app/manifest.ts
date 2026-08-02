import type { MetadataRoute } from "next";
import { COUNTRY_BRAND, serverCountry } from "@/lib/seo";

export default async function manifest(): Promise<MetadataRoute.Manifest> {
  const country = await serverCountry();
  const brand = COUNTRY_BRAND[country];
  return {
    name: brand,
    short_name: brand,
    description:
      country === "DE"
        ? "Rechtshilfe für Bürger und die digitale Kanzlei-Plattform"
        : "Ndihmë ligjore për qytetarët dhe platforma e zyrës ligjore",
    // "/" routes by role: logged-in lawyers → /dashboard, everyone else →
    // the citizen home. One PWA serves both audiences.
    start_url: "/",
    scope: "/",
    // Long-press shortcuts on the installed icon (citizen quick actions)
    shortcuts: [
      { name: "SOS", url: "/rasti-im?sos=1", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
      { name: "Ava", url: "/ava", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
      { name: "Rasti im", url: "/rasti-im", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
    ],
    display: "standalone",
    orientation: "any",
    background_color: "#f8fafc",
    theme_color: "#4338ca",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icons/icon-512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
