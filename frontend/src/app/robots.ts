import type { MetadataRoute } from "next";

// GEO/SEO: AI assistants and search engines may index every public page,
// but the lawyer workspace and account pages carry no public value.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/dashboard",
          "/assistant",
          "/billing",
          "/calendar",
          "/contacts",
          "/intake",
          "/marketplace",
          "/matters",
          "/platform",
          "/reports",
          "/settings",
          "/templates",
          "/portal",
          "/llogaria",
          "/rasti-im",
          "/login",
          "/kycu",
          "/onboarding",
          "/verifiko-email",
          "/rivendos",
          "/harrova-fjalekalimin",
          "/ftesa",
          "/api/",
        ],
      },
    ],
    sitemap: "https://avokatiim.ai/sitemap.xml",
  };
}
