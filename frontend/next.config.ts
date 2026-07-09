import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // The /api rewrite proxy defaults to 30s; Bora (LLM with thinking mode)
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
};

export default nextConfig;
