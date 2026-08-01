"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiDownload, apiGet, apiPost } from "@/lib/api";
import { localized, useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import { Doc, Matter, Template } from "@/lib/types";

interface AiAssistResult {
  improved_text: string;
  risk_flags: string[];
  changes: string[];
}
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
  const [aiInstruction, setAiInstruction] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [aiResult, setAiResult] = useState<AiAssistResult | null>(null);
  // True once an AI-improved draft was accepted into `output` — the saved
  // document then carries the ai_generated flag (BRAK human-review gate).
  const [aiUsed, setAiUsed] = useState(false);

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
      setAiUsed(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function improveWithAi() {
    if (!aiInstruction.trim() || !output) return;
    setAiBusy(true);
    setError("");
    try {
      const result = await apiPost<AiAssistResult>("/templates/ai-assist", {
        draft: output,
        instruction: aiInstruction.trim(),
      });
      setAiResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setAiBusy(false);
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
        ai_generated: aiUsed,
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

      <PageIntro k="templates" title={t.templatesIntroT} body={t.templatesIntro} />

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

              {/* AI clause assist: instruction → improved draft + risk flags */}
              <div className="border-t border-slate-100 pt-3 space-y-2">
                <p className="text-sm font-semibold text-slate-700">✦ {t.aiAssistTitle}</p>
                <div className="flex gap-2">
                  <Input
                    value={aiInstruction}
                    onChange={(e) => setAiInstruction(e.target.value)}
                    placeholder={t.aiAssistPlaceholder}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        improveWithAi();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={improveWithAi}
                    disabled={aiBusy || !aiInstruction.trim()}
                  >
                    {aiBusy ? t.loading : t.aiAssistRun}
                  </Button>
                </div>

                {aiResult && (
                  <div className="space-y-2 border border-indigo-200 bg-indigo-50/40 rounded-xl p-3">
                    {aiResult.risk_flags.length > 0 && (
                      <div className="text-xs bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 space-y-0.5">
                        <p className="font-semibold text-amber-800">⚠ {t.aiAssistRisks}</p>
                        {aiResult.risk_flags.map((f, i) => (
                          <p key={i} className="text-amber-700">• {f}</p>
                        ))}
                      </div>
                    )}
                    {aiResult.changes.length > 0 && (
                      <div className="text-xs text-slate-600 space-y-0.5">
                        <p className="font-semibold text-slate-700">{t.aiAssistChanges}</p>
                        {aiResult.changes.map((cItem, i) => (
                          <p key={i}>• {cItem}</p>
                        ))}
                      </div>
                    )}
                    <Textarea
                      rows={12}
                      value={aiResult.improved_text}
                      readOnly
                      className="text-sm font-serif leading-relaxed bg-white"
                    />
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        onClick={() => {
                          setOutput(aiResult.improved_text);
                          setAiResult(null);
                          setSavedDoc(null);
                          setAiUsed(true);
                        }}
                      >
                        {t.aiAssistAccept}
                      </Button>
                      <Button type="button" variant="secondary" onClick={() => setAiResult(null)}>
                        {t.aiAssistDiscard}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400 py-16 text-center">{t.selectTemplate}</p>
          )}
        </Card>
      </div>
    </div>
  );
}
