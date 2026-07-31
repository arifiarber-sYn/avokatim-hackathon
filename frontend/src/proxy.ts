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
  const response = NextResponse.next();
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
    response.headers.set(
      "Content-Security-Policy",
      [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://stats.avokatiim.ai",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' https://stats.avokatiim.ai wss: blob:",
        "media-src 'self' blob: data:",
        "worker-src 'self' blob:",
        "frame-ancestors 'none'",
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
