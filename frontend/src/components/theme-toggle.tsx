"use client";

/** Dark mode toggle (D-054 F5): light / dark / system, persisted in
 * localStorage and applied as .theme-dark on <html> (pre-paint script in
 * the root layout prevents the flash). */
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";

type ThemePref = "light" | "dark" | "system";

function apply(pref: ThemePref) {
  const dark =
    pref === "dark" ||
    (pref === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("theme-dark", dark);
}

export function ThemeToggle() {
  const { t } = useI18n();
  const [pref, setPref] = useState<ThemePref>("system");

  useEffect(() => {
    const saved = (localStorage.getItem("avokatim-theme") as ThemePref) || "system";
    setPref(saved);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if ((localStorage.getItem("avokatim-theme") || "system") === "system") apply("system");
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  function set(next: ThemePref) {
    setPref(next);
    localStorage.setItem("avokatim-theme", next);
    apply(next);
  }

  const options: { value: ThemePref; icon: string; label: string }[] = [
    { value: "light", icon: "☀", label: t.thLight },
    { value: "dark", icon: "☾", label: t.thDark },
    { value: "system", icon: "◐", label: t.thSystem },
  ];

  return (
    <div className="flex rounded-lg bg-slate-800 p-0.5" role="radiogroup" aria-label={t.thTheme}>
      {options.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={pref === o.value}
          title={o.label}
          onClick={() => set(o.value)}
          className={`flex-1 rounded-md px-2 py-1 text-xs transition ${
            pref === o.value ? "bg-slate-600 text-white" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {o.icon}
        </button>
      ))}
    </div>
  );
}
