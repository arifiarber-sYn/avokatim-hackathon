"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet, apiPost, getToken, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";
import { QuickTimer } from "@/components/quick-timer";
import { GlobalSearch } from "@/components/global-search";
import { NotificationBell } from "@/components/notification-bell";
import { ThemeToggle } from "@/components/theme-toggle";
import Brand from "@/components/brand";
import { InstallBanner } from "@/components/install-banner";
import AssistantPanel from "@/components/assistant-panel";

interface Me {
  full_name: string;
  email: string;
  is_superadmin?: boolean;
  email_verified?: boolean;
  tenant_plan?: string | null;
  tenant_trial_ends_at?: string | null;
  tenant_profession?: string;
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  // Unhandled /kontakti feedback — badge on the Platform nav item so the
  // operator sees new complaints/suggestions without any email ping.
  const [feedbackCount, setFeedbackCount] = useState(0);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    apiGet<Me>("/auth/me").then(setMe).catch(() => {});
    // Sliding session (D-054 F5): exchange the token for a fresh one so an
    // active lawyer is never logged out mid-work
    apiPost<{ access_token: string }>("/auth/refresh")
      .then((r) => setToken(r.access_token))
      .catch(() => {});
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, [router]);

  useEffect(() => {
    if (!me?.is_superadmin) return;
    apiGet<{ count: number }>("/platform/feedback/pending-count")
      .then((r) => setFeedbackCount(r.count))
      .catch(() => {});
  }, [me?.is_superadmin, pathname]);

  // Close the drawer on navigation
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  // Notary offices are impartial public officers: no case marketplace for them
  const isNotary = me?.tenant_profession === "notary";
  const nav = [
    { href: "/dashboard", label: t.dashboard, icon: "▦" },
    { href: "/matters", label: t.matters, icon: "▤" },
    { href: "/intake", label: t.intake, icon: "▷" },
    ...(isNotary ? [] : [{ href: "/marketplace", label: t.marketplace, icon: "◇" }]),
    { href: "/calendar", label: t.calendar, icon: "▧" },
    { href: "/contacts", label: t.contacts, icon: "◉" },
    { href: "/templates", label: t.templates, icon: "▣" },
    { href: "/assistant", label: t.assistant, icon: "✦" },
    { href: "/billing", label: t.billing, icon: "€" },
    { href: "/reports", label: t.analytics, icon: "◫" },
    { href: "/settings", label: t.settings, icon: "⚙" },
    ...(me?.is_superadmin ? [{ href: "/platform", label: t.platform, icon: "◈" }] : []),
  ];

  const trialDaysLeft =
    me?.tenant_plan === "trial" && me.tenant_trial_ends_at
      ? Math.max(
          0,
          Math.ceil(
            (new Date(me.tenant_trial_ends_at).getTime() - Date.now()) / 86_400_000
          )
        )
      : null;

  // The 4 primary destinations for the mobile bottom bar; the rest live in the drawer.
  const bottomNav = [
    { href: "/dashboard", label: t.dashboard, icon: "▦" },
    { href: "/matters", label: t.matters, icon: "▤" },
    { href: "/calendar", label: t.calendar, icon: "▧" },
    { href: "/assistant", label: t.assistant, icon: "✦" },
  ];

  const sidebarContent = (
    <>
      <div className="p-5 border-b border-slate-800">
        <h1 className="text-xl font-bold text-white">
          <Brand accentClass="text-indigo-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">{isNotary ? t.taglineNotary : t.tagline}</p>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              pathname.startsWith(item.href)
                ? "bg-indigo-600 text-white"
                : "hover:bg-slate-800 text-slate-300"
            }`}
          >
            <span className="w-4 text-center">{item.icon}</span>
            {item.label}
            {item.href === "/platform" && feedbackCount > 0 && (
              <span className="ml-auto rounded-full bg-rose-500 text-white text-[10px] font-semibold px-1.5 py-0.5 leading-none">
                {feedbackCount}
              </span>
            )}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-800 space-y-3">
        <QuickTimer />
        <ThemeToggle />
        <LocaleSwitcher up />
        {me && <p className="text-xs text-slate-400 truncate">{me.full_name}</p>}
        <button
          onClick={() => {
            setToken(null);
            router.push("/login");
          }}
          className="text-xs text-slate-400 hover:text-white"
        >
          {t.logout}
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-60 shrink-0 bg-slate-900 text-slate-200 flex-col">
        {sidebarContent}
      </aside>

      {/* Mobile top bar */}
      <header className="md:hidden fixed top-0 inset-x-0 z-40 h-14 bg-slate-900 text-white flex items-center justify-between px-4 shadow">
        <h1 className="text-lg font-bold">
          <Brand accentClass="text-indigo-400" />
        </h1>
        <div className="flex items-center gap-1">
          <NotificationBell dark />
          <button
            onClick={() => setDrawerOpen(true)}
            aria-label={t.menu}
            className="p-2 -mr-2 text-2xl leading-none"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setDrawerOpen(false)}
          />
          <aside className="relative w-72 max-w-[85vw] bg-slate-900 text-slate-200 flex flex-col h-full shadow-xl">
            <button
              onClick={() => setDrawerOpen(false)}
              aria-label={t.close}
              className="absolute top-4 right-4 text-slate-400 text-xl leading-none"
            >
              ✕
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}

      {/* Mobile bottom navigation */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-slate-200 flex justify-around pb-[env(safe-area-inset-bottom)]">
        {bottomNav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center gap-0.5 py-2 px-3 text-[10px] ${
              pathname.startsWith(item.href)
                ? "text-indigo-600 font-semibold"
                : "text-slate-500"
            }`}
          >
            <span className="text-lg leading-none">{item.icon}</span>
            {item.label}
          </Link>
        ))}
        <button
          onClick={() => setDrawerOpen(true)}
          className="flex flex-col items-center gap-0.5 py-2 px-3 text-[10px] text-slate-500"
        >
          <span className="text-lg leading-none">☰</span>
          {t.more}
        </button>
      </nav>

      <main className="flex-1 min-w-0 p-4 pt-18 pb-20 md:p-6 md:pt-6 md:pb-6 lg:p-8 overflow-auto">
        <div className="mb-4 flex items-center gap-2">
          <GlobalSearch />
          <div className="hidden md:block">
            <NotificationBell />
          </div>
        </div>
        {trialDaysLeft !== null && (
          <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-2">
            {t.trialBanner.replace("{days}", String(trialDaysLeft))}
          </div>
        )}
        {me && me.email_verified === false && (
          <div className="mb-4 rounded-lg bg-sky-50 border border-sky-200 text-sky-800 text-sm px-4 py-2 flex items-center justify-between gap-3 flex-wrap">
            <span>{t.verifyEmailBanner}</span>
            <button
              onClick={() => {
                apiPost("/auth/resend-verification", {}).catch(() => {});
              }}
              className="text-sky-700 underline text-xs py-1.5 -my-1.5"
            >
              {t.resendVerification}
            </button>
          </div>
        )}
        {children}
      </main>

      {/* Ava everywhere (D-052): contextual assistant panel, hidden on /assistant */}
      <AssistantPanel />
      <InstallBanner />
    </div>
  );
}
