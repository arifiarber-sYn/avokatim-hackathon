"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiDownload, apiGet, apiPost } from "@/lib/api";
import { localized, useI18n } from "@/lib/i18n";
import { Doc, Matter, Template } from "@/lib/types";
import { Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea } from "@/components/ui";

export default function TemplatesPage() {
  const { t, locale } = useI18n();
  const [templates, setTemplates] = useState<Template[] | null>(null);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [matterId, setMatterId] = useState("");
  const [values, setValues] = useState<Record<string, string>>({});
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [savedDoc, setSavedDoc] = useState<Doc | null>(null);

  useEffect(() => {
    apiGet<Template[]>("/templates?jurisdiction_code=XK").then(setTemplates).catch(() => {});
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => {});
  }, []);

  const selected = templates?.find((tpl) => tpl.id === templateId);

  async function render(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSavedDoc(null);
    try {
      const result = await apiPost<{ content: string }>("/templates/render", {
        template_id: templateId,
        matter_id: matterId || null,
        variables: values,
      });
      setOutput(result.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function saveToMatter() {
    if (!matterId) return;
    setSaving(true);
    setError("");
    try {
      const doc = await apiPost<Doc>("/templates/render-to-matter", {
        template_id: templateId,
        matter_id: matterId,
        variables: values,
        content: output,
      });
      setSavedDoc(doc);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setSaving(false);
    }
  }

  if (templates === null) return <Spinner />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t.generateDocument}</h1>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <form onSubmit={render} className="space-y-4">
            <div>
              <Label>{t.selectTemplate}</Label>
              <Select
                value={templateId}
                onChange={(e) => {
                  setTemplateId(e.target.value);
                  setValues({});
                  setOutput("");
                  setSavedDoc(null);
                }}
                required
              >
                <option value="">—</option>
                {templates.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {localized(tpl.name, locale)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t.selectMatter}</Label>
              <Select value={matterId} onChange={(e) => setMatterId(e.target.value)}>
                <option value="">—</option>
                {matters.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.reference} — {m.title}
                  </option>
                ))}
              </Select>
            </div>

            {selected?.variables.map((v) => (
              <div key={v.name}>
                <Label>{localized(v.label, locale) || v.name}</Label>
                <Textarea
                  rows={2}
                  value={values[v.name] || ""}
                  onChange={(e) => setValues({ ...values, [v.name]: e.target.value })}
                />
              </div>
            ))}

            <ErrorNote message={error} />
            <Button type="submit" disabled={busy || !templateId}>
              {busy ? t.loading : t.render}
            </Button>
          </form>
        </Card>

        <Card className="p-5">
          {output ? (
            <div className="space-y-3">
              <div className="flex gap-2 flex-wrap items-center">
                {matterId && (
                  <Button onClick={saveToMatter} disabled={saving || !!savedDoc}>
                    {saving ? t.loading : savedDoc ? "✓" : t.saveToMatter}
                  </Button>
                )}
                <Button
                  variant="secondary"
                  onClick={() => {
                    navigator.clipboard.writeText(output);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                  }}
                >
                  {copied ? t.copied : t.copyText}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    const name = selected ? localized(selected.name, locale) : "dokument";
                    apiDownload(`/templates/render-docx`, `${name}.docx`, {
                      method: "POST",
                      body: {
                        template_id: templateId,
                        matter_id: matterId || null,
                        variables: values,
                        content: output,
                      },
                    });
                  }}
                >
                  {t.downloadDocx}
                </Button>
              </div>
              {savedDoc && (
                <p className="text-sm text-emerald-700">
                  ✓ {t.savedToMatter} —{" "}
                  <Link
                    href={`/matters/${matterId}`}
                    className="underline hover:text-emerald-900"
                  >
                    {matters.find((m) => m.id === matterId)?.reference}
                  </Link>
                </p>
              )}
              <Textarea
                rows={22}
                value={output}
                onChange={(e) => {
                  setOutput(e.target.value);
                  setSavedDoc(null);
                }}
                className="text-sm font-serif leading-relaxed bg-slate-50"
              />
            </div>
          ) : (
            <p className="text-sm text-slate-400 py-16 text-center">{t.selectTemplate}</p>
          )}
        </Card>
      </div>
    </div>
  );
}
