"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { dictionaries, Dictionary, Locale } from "./dictionaries";

interface I18nContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: Dictionary;
}

const I18nContext = createContext<I18nContextValue>({
  locale: "sq",
  setLocale: () => {},
  t: dictionaries.sq,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("sq");

  useEffect(() => {
    const saved = localStorage.getItem("boralaw_locale") as Locale | null;
    if (saved && dictionaries[saved]) setLocaleState(saved);
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("boralaw_locale", l);
  };

  return (
    <I18nContext.Provider value={{ locale, setLocale, t: dictionaries[locale] }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}

export function localized(name: Record<string, string> | undefined, locale: Locale): string {
  if (!name) return "";
  return name[locale] || name.sq || name.en || Object.values(name)[0] || "";
}
