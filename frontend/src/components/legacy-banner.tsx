import type { Country } from "@/lib/country";
import { dictionaries } from "@/lib/dictionaries";

/*
 * Graceful degradation for old browsers and disabled JS (D-063, the Vuksani
 * lesson: a lawyer's ancient in-app browser silently showed a broken page).
 *
 * Rendered server-side BEFORE React hydrates, so it works exactly where the
 * app itself cannot. Two layers:
 *  - <noscript>: JS off entirely (strict in-app browsers, privacy modes).
 *  - inline ES5 probe: parses modern syntax with `new Function`; if the
 *    engine is too old to run our Next.js bundle, a visible banner tells the
 *    visitor to open the page in an up-to-date Chrome/Safari instead of
 *    leaving them staring at a half-dead page.
 *
 * Texts come from dictionaries.ts but are fixed to the host's default locale
 * (sq for XK, de for DE) — the language switcher needs JS, which is the very
 * thing missing here.
 */

const BANNER_STYLE =
  "background:#7f1d1d;color:#fff;padding:12px 16px;font:14px/1.5 sans-serif;text-align:center";

export default function LegacyBanner({ country }: { country: Country }) {
  const t = dictionaries[country === "DE" ? "de" : "sq"];
  const probe = [
    "(function(){try{new Function('var a={};a?.b;a??1;async function f(){}')}catch(e){",
    "var d=document.createElement('div');",
    `d.setAttribute('style','${BANNER_STYLE}');`,
    `d.textContent=${JSON.stringify(t.legacyBrowserWarn)};`,
    "document.body.insertBefore(d,document.body.firstChild);}})();",
  ].join("");
  return (
    <>
      <noscript>
        <div style={{
          background: "#7f1d1d", color: "#fff", padding: "12px 16px",
          font: "14px/1.5 sans-serif", textAlign: "center",
        }}>
          {t.noscriptWarn}
        </div>
      </noscript>
      <script dangerouslySetInnerHTML={{ __html: probe }} />
    </>
  );
}
