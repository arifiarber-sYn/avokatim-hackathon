"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet, getToken, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LocaleSwitcher } from "@/components/ui";
import { QuickTimer } from "@/components/quick-timer";

interface Me {
  full_name: string;
  email: string;
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    apiGet<Me>("/auth/me").then(setMe).catch(() => {});
  }, [router]);

  const nav = [
    { href: "/dashboard", label: t.dashboard, icon: "▦" },
    { href: "/matters", label: t.matters, icon: "▤" },
    { href: "/intake", label: t.intake, icon: "▷" },
    { href: "/calendar", label: t.calendar, icon: "▧" },
    { href: "/contacts", label: t.contacts, icon: "◉" },
    { href: "/templates", label: t.templates, icon: "▣" },
    { href: "/assistant", label: t.assistant, icon: "✦" },
    { href: "/billing", label: t.billing, icon: "€" },
    { href: "/reports", label: t.analytics, icon: "◫" },
    { href: "/settings", label: t.settings, icon: "⚙" },
  ];

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 bg-slate-900 text-slate-200 flex flex-col">
        <div className="p-5 border-b border-slate-800">
          <h1 className="text-xl font-bold text-white">
            Bora<span className="text-indigo-400">Law</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">{t.tagline}</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
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
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-800 space-y-3">
          <QuickTimer />
          <LocaleSwitcher />
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
      </aside>
      <main className="flex-1 min-w-0 p-6 lg:p-8 overflow-auto">{children}</main>
    </div>
  );
}
