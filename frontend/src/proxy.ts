import { NextRequest, NextResponse } from "next/server";

// TLS terminates at Cloudflare's edge (tunnel), so the app itself only sees
// plain HTTP. Cloudflare forwards the visitor's original scheme in
// x-forwarded-proto: redirect plain-http visitors to https and pin browsers
// there with HSTS. Local/LAN access (no x-forwarded-proto) is untouched.
export function proxy(request: NextRequest) {
  // Next itself synthesizes x-forwarded-proto for direct connections, so
  // gate on the public hostname too — local (127.0.0.1:3000) and LAN access
  // must keep working over plain http.
  const host = request.headers.get("host") || "";
  const isPublicHost = host === "avokatiim.ai" || host.endsWith(".avokatiim.ai");
  const proto = request.headers.get("x-forwarded-proto");
  if (isPublicHost && proto === "http") {
    // nextUrl carries the internal origin (localhost:3000) — rebuild from
    // the public Host header instead
    const { pathname, search } = request.nextUrl;
    return NextResponse.redirect(`https://${host}${pathname}${search}`, 301);
  }
  // Country scoping (D-034): de.avokatiim.ai serves Germany, everything else
  // Kosovo. The header rides along on page renders (server components read
  // it via headers()) and on the /api rewrite to the backend, which trusts
  // it only for public endpoints.
  const country = host.split(":")[0].toLowerCase() === "de.avokatiim.ai" ? "DE" : "XK";
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-avokatim-country", country);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  if (isPublicHost && proto === "https") {
    response.headers.set("Strict-Transport-Security", "max-age=31536000");
  }
  if (isPublicHost) {
    // Security headers (D-033). CSP notes: Next.js hydration needs inline
    // scripts (no nonce infra yet), so 'unsafe-inline' stays for now — the
    // real win is locking script/connect origins so an injected payload
    // cannot load or exfiltrate to an attacker domain. stats.avokatiim.ai
    // is the self-hosted Umami; wss:/blob: cover LiveKit SOS calls and
    // voice recording; data:/blob: images cover lawyer photos and previews.
    // /outlook only (D-059 F8): the add-in taskpane loads Office.js from
    // the Microsoft CDN and runs inside an Outlook iframe — the exception
    // is scoped to this one route, everything else keeps 'none'.
    const isOutlook = request.nextUrl.pathname.startsWith("/outlook");
    response.headers.set(
      "Content-Security-Policy",
      [
        "default-src 'self'",
        // static.cloudflareinsights.com: Cloudflare injects its RUM beacon on
        // proxied hosts; blocking it spams every visitor's console (D-063).
        "script-src 'self' 'unsafe-inline' https://stats.avokatiim.ai https://static.cloudflareinsights.com" +
          (isOutlook ? " https://appsforoffice.microsoft.com https://ajax.aspnetcdn.com" : ""),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' https://stats.avokatiim.ai https://cloudflareinsights.com wss: blob:" +
          (isOutlook ? " https://appsforoffice.microsoft.com" : ""),
        "media-src 'self' blob: data:",
        "worker-src 'self' blob:",
        isOutlook
          ? "frame-ancestors https://outlook.office.com https://outlook.office365.com https://outlook.live.com"
          : "frame-ancestors 'none'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
      ].join("; "),
    );
    response.headers.set("X-Content-Type-Options", "nosniff");
    response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
    response.headers.set(
      "Permissions-Policy",
      // camera/mic stay first-party — the SOS video call needs them
      "camera=(self), microphone=(self), geolocation=(), payment=(), usb=()",
    );
  }
  return response;
}

export const config = {
  // Skip static assets; they are only ever referenced from pages that
  // already went through the redirect
  matcher: ["/((?!_next/static|_next/image|icons/|favicon.ico).*)"],
};
