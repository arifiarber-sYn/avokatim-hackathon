"use client";

/**
 * Shared shell for the citizen-facing public pages (/, /ava, /avokatet,
 * /posto-rastin, /rasti-im). Desktop gets a slim header with text links;
 * mobile gets an app-like persistent bottom navigation in the thumb zone
 * with the SOS action elevated in the center (safety-app pattern).
 */
import { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";

function AvaIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z" strokeLinejoin="round" />
      <circle cx="9.5" cy="12" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="13" cy="12" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="16.5" cy="12" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  );
}

function LawyersIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" strokeLinecap="round" />
      <path d="M16.5 4.5a3.5 3.5 0 0 1 0 7M21 20c0-2.8-1.9-5.1-4.5-5.8" strokeLinecap="round" />
    </svg>
  );
}

function PostIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M12 5v14M5 12h14" strokeLinecap="round" />
    </svg>
  );
}

function CaseIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

const NAV = [
  { href: "/ava", label: (t: Record<string, string>) => "Ava", Icon: AvaIcon },
  { href: "/avokatet", label: (t: Record<string, string>) => t.pnLawyers, Icon: LawyersIcon },
  { href: "/posto-rastin", label: (t: Record<string, string>) => t.pnPost, Icon: PostIcon },
  { href: "/rasti-im", label: (t: Record<string, string>) => t.mkMyCase, Icon: CaseIcon },
];

export default function PublicShell({
  children,
  wide = false,
}: {
  children: ReactNode;
  wide?: boolean;
}) {
  const { t } = useI18n();
  const pathname = usePathname();
  const dict = t as unknown as Record<string, string>;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className={`${wide ? "max-w-5xl" : "max-w-2xl"} mx-auto px-4 py-3 flex items-center justify-between gap-3`}>
          <Link href="/" className="text-lg font-bold text-indigo-700 shrink-0">
            Avokat<span className="text-slate-900">IM</span>
          </Link>
          <nav className="hidden md:flex items-center gap-5">
            {NAV.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={`text-sm hover:text-indigo-700 ${
                  pathname.startsWith(href) ? "text-indigo-700 font-semibold" : "text-slate-600"
                }`}
              >
                {label(dict)}
              </Link>
            ))}
            <Link
              href="/rasti-im?sos=1"
              className="text-sm font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg px-3 py-1.5"
            >
              SOS
            </Link>
          </nav>
          <div className="flex items-center gap-3 shrink-0">
            <Link
              href="/per-avokatet"
              className="hidden sm:block text-xs text-slate-400 hover:text-slate-600 hover:underline"
            >
              {t.mkForLawyersLink}
            </Link>
            <LocaleSwitcher />
          </div>
        </div>
      </header>

      {/* pb keeps content clear of the fixed bottom nav on mobile */}
      <div className="flex-1 flex flex-col pb-20 md:pb-0">{children}</div>

      <nav
        className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-slate-200"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="flex items-end justify-around">
          {NAV.slice(0, 2).map(({ href, label, Icon }) => (
            <BottomItem key={href} href={href} label={label(dict)} Icon={Icon} active={pathname.startsWith(href)} />
          ))}
          {/* Elevated SOS in the dead center — the most thumb-reachable spot */}
          <Link
            href="/rasti-im?sos=1"
            className="flex flex-col items-center justify-center -mt-5 h-14 w-14 rounded-full bg-red-600 text-white text-xs font-extrabold shadow-lg shrink-0"
            aria-label="SOS"
          >
            SOS
          </Link>
          {NAV.slice(2).map(({ href, label, Icon }) => (
            <BottomItem key={href} href={href} label={label(dict)} Icon={Icon} active={pathname.startsWith(href)} />
          ))}
        </div>
      </nav>
    </div>
  );
}

function BottomItem({
  href,
  label,
  Icon,
  active,
}: {
  href: string;
  label: string;
  Icon: (props: { className?: string }) => ReactNode;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex flex-col items-center gap-0.5 py-2 min-w-[64px] min-h-[48px] justify-center ${
        active ? "text-indigo-700" : "text-slate-400"
      }`}
    >
      <Icon className="h-5 w-5" />
      <span className={`text-[10px] ${active ? "font-semibold" : ""}`}>{label}</span>
    </Link>
  );
}
