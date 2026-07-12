"use client";

/**
 * Shared shell for the citizen-facing public pages (/, /ava, /avokatet,
 * /posto-rastin, /rasti-im). Desktop gets a slim header with text links;
 * mobile gets an app-like persistent bottom navigation in the thumb zone
 * with the SOS action elevated in the center (safety-app pattern).
 */
import { ReactNode, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";
import PublicFooter from "@/components/public-footer";
import {
  CitizenInfo,
  citizenGet,
  getCitizenToken,
  setCitizenToken,
} from "@/lib/citizen";

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

/** Header chip for a signed-in citizen: initials -> menu (my case, account, sign out). */
function CitizenChip({ citizen }: { citizen: CitizenInfo }) {
  const { t } = useI18n();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const initials = citizen.full_name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full bg-indigo-50 hover:bg-indigo-100 pl-1 pr-3 py-1 transition"
        aria-label={t.acctTitle}
      >
        <span className="h-7 w-7 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
          {initials || "?"}
        </span>
        <span className="hidden sm:block text-sm font-medium text-indigo-900 max-w-[10rem] truncate">
          {citizen.full_name.split(/\s+/)[0]}
        </span>
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-lg py-2 w-52 z-50">
          <Link
            href="/rasti-im"
            className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-indigo-700"
            onClick={() => setOpen(false)}
          >
            {t.mkMyCase}
          </Link>
          <Link
            href="/llogaria"
            className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-indigo-700"
            onClick={() => setOpen(false)}
          >
            {t.acctTitle}
          </Link>
          <button
            className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
            onClick={() => {
              setCitizenToken(null);
              setOpen(false);
              router.push("/");
              router.refresh();
            }}
          >
            {t.acctLogout}
          </button>
        </div>
      )}
    </div>
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
  footer = true,
}: {
  children: ReactNode;
  wide?: boolean;
  footer?: boolean;
}) {
  const { t } = useI18n();
  const pathname = usePathname();
  const dict = t as unknown as Record<string, string>;
  const toolsActive = pathname.startsWith("/afatet") || pathname.startsWith("/dokumentet");

  // Recognize a signed-in citizen so their credentials never lead them to
  // the lawyer login: valid token -> chip menu, stale token -> cleared.
  const [citizen, setCitizen] = useState<CitizenInfo | null>(null);
  useEffect(() => {
    if (!getCitizenToken()) return;
    citizenGet<CitizenInfo>("/citizen/me")
      .then(setCitizen)
      .catch((err) => {
        if ((err as { status?: number }).status === 401) setCitizenToken(null);
      });
  }, [pathname]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white/85 backdrop-blur border-b border-slate-200 sticky top-0 z-40">
        <div className={`${wide ? "max-w-5xl" : "max-w-2xl"} mx-auto px-4 py-3 flex items-center justify-between gap-3`}>
          <Link href="/" className="flex items-center gap-2 text-lg font-bold text-indigo-700 shrink-0">
            <span className="h-8 w-8 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white flex items-center justify-center shadow-sm">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
                <path d="M12 3v18M5 21h14M12 6l6 2M12 6L6 8" strokeLinecap="round" />
                <path d="M4 13l2-5 2 5a2.5 2.5 0 0 1-4 0zM16 13l2-5 2 5a2.5 2.5 0 0 1-4 0z" strokeLinejoin="round" />
              </svg>
            </span>
            <span>
              Avokat<span className="text-slate-900">IM</span>
            </span>
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
            {/* Tools dropdown: deadline calculator + document generator */}
            <div className="relative group">
              <span
                className={`text-sm cursor-default group-hover:text-indigo-700 ${
                  toolsActive ? "text-indigo-700 font-semibold" : "text-slate-600"
                }`}
              >
                {t.pnTools} ▾
              </span>
              <div className="absolute left-0 top-full pt-2 hidden group-hover:block">
                <div className="bg-white border border-slate-200 rounded-xl shadow-lg py-2 w-64">
                  <Link href="/afatet" className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-indigo-700">
                    {t.dcTitle}
                  </Link>
                  <Link href="/dokumentet" className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-indigo-700">
                    {t.cdTitle}
                  </Link>
                </div>
              </div>
            </div>
            <Link
              href="/rasti-im?sos=1"
              className="text-sm font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg px-3 py-1.5"
            >
              SOS
            </Link>
          </nav>
          <div className="flex items-center gap-3 shrink-0">
            {!citizen && (
              <Link
                href="/per-avokatet"
                className="hidden sm:block text-xs text-slate-400 hover:text-slate-600 hover:underline"
              >
                {t.mkForLawyersLink}
              </Link>
            )}
            <LocaleSwitcher />
            {citizen ? (
              <CitizenChip citizen={citizen} />
            ) : (
              <Link
                href="/kycu"
                className="text-sm font-semibold text-indigo-700 hover:text-indigo-900"
              >
                {t.login}
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* pb keeps content clear of the fixed bottom nav on mobile */}
      <div className="flex-1 flex flex-col pb-20 md:pb-0">
        <div className="flex-1 flex flex-col">{children}</div>
        {footer && <PublicFooter />}
      </div>

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
