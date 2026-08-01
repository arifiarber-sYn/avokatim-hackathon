"use client";

// Public RVG fee calculator ("Was kostet ein Anwalt?") for the German host,
// over the data-driven § 13 RVG table. Information, not legal advice.
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { clientCountry } from "@/lib/country";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import { Button, Card, ErrorNote, Input, Label, Select } from "@/components/ui";
import { IconScale } from "@/components/icons";

interface VvItem {
  code: string;
  vv: string;
  rate: string;
  group: string;
  name: Record<string, string>;
}

interface FeeLine {
  code: string;
  vv: string;
  name: Record<string, string>;
  rate: string | null;
  amount: string;
}

interface FeeResult {
  value: string;
  base_fee: string;
  legal_basis: string;
  lines: FeeLine[];
  net: string;
  vat_rate: number;
  vat: string;
  total: string;
}

const GG_RATES = ["0.5", "0.8", "1.0", "1.3", "1.5", "1.8", "2.0", "2.5"];

export default function RvgCalcPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [items, setItems] = useState<VvItem[]>([]);
  const [value, setValue] = useState("");
  const [selected, setSelected] = useState<string[]>(["geschaeftsgebuehr"]);
  const [ggRate, setGgRate] = useState("1.3");
  const [result, setResult] = useState<FeeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (clientCountry() !== "DE") {
      router.replace("/");
      return;
    }
    fetch("/api/public/tools/fee-items")
      .then((res) => (res.ok ? res.json() : { items: [] }))
      .then((data) => setItems(data.items || []))
      .catch(() => setItems([]));
  }, [router]);

  const label = useMemo(
    () => (name: Record<string, string>) => name[locale] || name.de || name.sq,
    [locale]
  );

  function toggle(code: string) {
    setResult(null);
    setSelected((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  }

  async function calc(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/public/tools/fee-calc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          value_eur: Number(value),
          items: selected,
          geschaeftsgebuehr_rate: selected.includes("geschaeftsgebuehr")
            ? Number(ggRate)
            : undefined,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || t.error);
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  const groups: { key: string; title: string }[] = [
    { key: "aussergerichtlich", title: t.rvgOutOfCourt },
    { key: "gerichtlich", title: t.rvgInCourt },
  ];

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <IconScale className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.rvgTitle}</h1>
        </div>

        <PageIntro k="rvg" title={t.rvgIntroT} body={t.rvgIntro} />

        <Card className="p-5 space-y-4">
          <form onSubmit={calc} className="space-y-4">
            <div>
              <Label>{t.rvgValue}</Label>
              <Input
                type="number"
                min="1"
                step="1"
                value={value}
                onChange={(e) => { setValue(e.target.value); setResult(null); }}
                required
              />
              <p className="text-xs text-slate-400 mt-1">{t.rvgValueHint}</p>
            </div>

            <div className="space-y-3">
              <Label>{t.rvgItems}</Label>
              {groups.map((group) => (
                <div key={group.key} className="space-y-1.5">
                  <p className="text-xs font-semibold text-slate-500">{group.title}</p>
                  {items
                    .filter((item) => item.group === group.key)
                    .map((item) => (
                      <label key={item.code} className="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={selected.includes(item.code)}
                          onChange={() => toggle(item.code)}
                          className="rounded border-slate-300"
                        />
                        <span>
                          {label(item.name)}{" "}
                          <span className="text-slate-400">
                            ({item.vv} · {item.rate})
                          </span>
                        </span>
                      </label>
                    ))}
                </div>
              ))}
            </div>

            {selected.includes("geschaeftsgebuehr") && (
              <div>
                <Label>{t.rvgGgRate}</Label>
                <Select value={ggRate} onChange={(e) => { setGgRate(e.target.value); setResult(null); }}>
                  {GG_RATES.map((r) => (
                    <option key={r} value={r}>{r.replace(".", ",")}</option>
                  ))}
                </Select>
              </div>
            )}

            <ErrorNote message={error} />
            <Button type="submit" disabled={busy || !value || selected.length === 0} className="w-full">
              {busy ? t.loading : t.rvgCalc}
            </Button>
          </form>

          {result && (
            <div className="rounded-xl bg-indigo-50 border border-indigo-200 p-4 space-y-2">
              <p className="text-xs text-indigo-700">
                {t.rvgBaseFee}: {Number(result.base_fee).toFixed(2)} € · {result.legal_basis}
              </p>
              <div className="space-y-1">
                {result.lines.map((line, i) => (
                  <div key={i} className="flex justify-between text-sm text-indigo-900">
                    <span>
                      {label(line.name)}{" "}
                      <span className="text-indigo-400">({line.vv})</span>
                    </span>
                    <span className="font-mono">{Number(line.amount).toFixed(2)} €</span>
                  </div>
                ))}
              </div>
              <div className="border-t border-indigo-200 pt-2 text-sm text-indigo-900 space-y-0.5">
                <div className="flex justify-between">
                  <span>{t.rvgNet}</span>
                  <span className="font-mono">{Number(result.net).toFixed(2)} €</span>
                </div>
                <div className="flex justify-between">
                  <span>{t.vat} {result.vat_rate}%</span>
                  <span className="font-mono">{Number(result.vat).toFixed(2)} €</span>
                </div>
                <div className="flex justify-between font-bold text-base">
                  <span>{t.rvgTotalGross}</span>
                  <span className="font-mono">{Number(result.total).toFixed(2)} €</span>
                </div>
              </div>
            </div>
          )}
        </Card>

        <p className="text-xs text-slate-400">{t.rvgDisclaimer}</p>
      </main>
    </PublicShell>
  );
}
