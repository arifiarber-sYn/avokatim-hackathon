"use client";

// Public self-service document generator (no account needed): plain-language
// fields -> formal letter PDF from deterministic templates. Not legal advice.
import { useEffect, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import { Button, Card, ErrorNote, Input, Label, Spinner, Textarea } from "@/components/ui";
import { IconDoc } from "@/components/icons";

interface DocField {
  key: string;
  type: string;
  label: Record<string, string>;
}

interface DocTemplate {
  code: string;
  category: string;
  name: Record<string, string>;
  fields: DocField[];
  requires_notary: boolean;
  notary_act: string | null;
}

const CATEGORY_ORDER = ["institucionet", "puna", "konsumatori", "te_pergjithshme", "noteria"];

export default function CitizenDocsPage() {
  const { t, locale } = useI18n();
  const [templates, setTemplates] = useState<DocTemplate[] | null>(null);
  const [picked, setPicked] = useState<DocTemplate | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/public/tools/documents")
      .then((res) => res.json())
      .then(setTemplates)
      .catch(() => setTemplates([]));
  }, []);

  const loc = (m: Record<string, string>) => m[locale] || m.sq || "";

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    if (!picked) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`/api/public/tools/documents/${picked.code}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || t.error);
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `${picked.code}-avokatim.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <IconDoc className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.cdTitle}</h1>
        </div>

        <PageIntro k="dokumentet" title={t.cdIntroT} body={t.cdIntro} />

        {templates === null ? (
          <Spinner />
        ) : !picked ? (
          <div className="space-y-5">
            <p className="text-sm font-semibold text-slate-600">{t.cdPick}</p>
            {CATEGORY_ORDER.filter((cat) => templates.some((tpl) => tpl.category === cat)).map(
              (cat) => {
                const catLabel = {
                  institucionet: t.cdCatInstitucionet,
                  puna: t.cdCatPuna,
                  konsumatori: t.cdCatKonsumatori,
                  te_pergjithshme: t.cdCatTePergjithshme,
                  noteria: t.cdCatNoteria,
                }[cat];
                return (
                  <div key={cat} className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      {catLabel}
                    </p>
                    {templates
                      .filter((tpl) => tpl.category === cat)
                      .map((tpl) => (
                        <button
                          key={tpl.code}
                          onClick={() => {
                            setPicked(tpl);
                            setValues({});
                          }}
                          className="w-full text-left bg-white rounded-xl border border-slate-200 p-4 hover:border-indigo-300 hover:shadow-sm transition flex items-center gap-3"
                        >
                          <IconDoc className="h-5 w-5 text-indigo-600 shrink-0" />
                          <p className="font-semibold text-slate-900 flex-1">{loc(tpl.name)}</p>
                          {tpl.requires_notary && (
                            <span className="text-[11px] font-semibold bg-amber-100 text-amber-800 rounded-full px-2 py-0.5 shrink-0">
                              {t.pnNotaries}
                            </span>
                          )}
                        </button>
                      ))}
                  </div>
                );
              }
            )}
          </div>
        ) : (
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">{loc(picked.name)}</h2>
              <button
                onClick={() => setPicked(null)}
                className="text-xs text-slate-400 hover:text-indigo-600 hover:underline shrink-0"
              >
                {t.cdOther}
              </button>
            </div>
            {picked.requires_notary && (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 space-y-1.5">
                <p className="text-xs text-amber-800">⚠ {t.cdNotaryFlag}</p>
                <Link href="/noteret" className="block text-xs font-semibold text-indigo-600 hover:underline">
                  {t.cdNotaryLink} →
                </Link>
              </div>
            )}
            <form onSubmit={generate} className="space-y-3">
              {picked.fields.map((field) => (
                <div key={field.key}>
                  <Label>{loc(field.label)}</Label>
                  {field.type === "textarea" ? (
                    <Textarea
                      rows={4}
                      value={values[field.key] || ""}
                      onChange={(e) => setValues({ ...values, [field.key]: e.target.value })}
                      required
                    />
                  ) : (
                    <Input
                      value={values[field.key] || ""}
                      onChange={(e) => setValues({ ...values, [field.key]: e.target.value })}
                      required
                    />
                  )}
                </div>
              ))}
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy} className="w-full">
                {busy ? t.loading : `⬇ ${t.cdGenerate}`}
              </Button>
            </form>
          </Card>
        )}

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.cdDisclaimer}</p>
      </main>
    </PublicShell>
  );
}
