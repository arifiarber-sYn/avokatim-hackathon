import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // The /api rewrite proxy defaults to 30s; Ava (LLM with thinking mode)
    // can take longer, which surfaced as "NetworkError" in the browser.
    // Match the backend's LLM timeout (180s) with headroom.
    proxyTimeout: 300_000,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
  // German visitors on de.avokatiim.ai type/guess German slugs (mobile audit
  // D-063 confirmed people land on them) — route names are Albanian, so
  // catch the obvious German equivalents instead of serving a 404.
  async redirects() {
    return [
      { source: "/fuer-anwaelte", destination: "/per-avokatet", permanent: true },
      { source: "/für-anwälte", destination: "/per-avokatet", permanent: true },
      { source: "/fuer-notare", destination: "/per-noteret", permanent: true },
      { source: "/fuer-buerger", destination: "/per-qytetaret", permanent: true },
      { source: "/anmelden", destination: "/kycu", permanent: true },
      { source: "/registrieren", destination: "/regjistrohu", permanent: true },
      { source: "/fall-posten", destination: "/posto-rastin", permanent: true },
      { source: "/mein-fall", destination: "/rasti-im", permanent: true },
      { source: "/kontakt", destination: "/kontakti", permanent: true },
      { source: "/anwaelte", destination: "/avokatet", permanent: true },
      { source: "/notare", destination: "/noteret", permanent: true },
    ];
  },
};

export default nextConfig;
