"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { localized, useI18n } from "@/lib/i18n";
import { Matter, Template } from "@/lib/types";
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
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    apiGet<Template[]>("/templates?jurisdiction_code=XK").then(setTemplates).catch(() => {});
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => {});
  }, []);

  const selected = templates?.find((tpl) => tpl.id === templateId);

  async function render(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
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
              <pre className="text-sm whitespace-pre-wrap font-serif leading-relaxed bg-slate-50 rounded-lg p-4 max-h-[70vh] overflow-auto">
                {output}
              </pre>
            </div>
          ) : (
            <p className="text-sm text-slate-400 py-16 text-center">{t.selectTemplate}</p>
          )}
        </Card>
      </div>
    </div>
  );
}
