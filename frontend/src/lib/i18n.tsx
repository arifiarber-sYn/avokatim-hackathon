"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { clientCountry } from "./country";
import { dictionaries, Dictionary, Locale } from "./dictionaries";

// DE rebrand (D-056): the German host trades under "Ava Legal" while Kosovo
// keeps "AvokatIM". Rather than forking 9000+ dictionary strings, every
// string is passed through this single replacement when the host is DE.
function rebrand(dict: Dictionary): Dictionary {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(dict)) {
    out[key] = (value as string).split("AvokatIM").join("Ava Legal");
  }
  return out as unknown as Dictionary;
}

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
  // Resolved after mount (not during SSR) so server and first client render
  // agree; the brand swaps in with the same hydration pass as the locale.
  const [isDE, setIsDE] = useState(false);

  useEffect(() => {
    setIsDE(clientCountry() === "DE");
    const saved = localStorage.getItem("avokatim_locale") as Locale | null;
    if (saved && dictionaries[saved]) {
      setLocaleState(saved);
    } else if (clientCountry() === "DE") {
      // German host, no saved preference — German-first (D-034)
      setLocaleState("de");
    }
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("avokatim_locale", l);
  };

  const t = useMemo(
    () => (isDE ? rebrand(dictionaries[locale]) : dictionaries[locale]),
    [locale, isDE]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
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
