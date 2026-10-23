"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import PageIntro from "@/components/page-intro";
import { Intake } from "@/lib/types";
import { Badge, Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea } from "@/components/ui";

export default function IntakePage() {
  const { t } = useI18n();
  const router = useRouter();
  const [intakes, setIntakes] = useState<Intake[] | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    client_name: "",
    client_email: "",
    client_phone: "",
    opposing: "",
    summary: "",
    source: "referral",
  });

  const load = useCallback(() => {
    apiGet<Intake[]>("/intake").then(setIntakes).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiPost("/intake", {
        client_name: form.client_name,
        client_email: form.client_email || null,
        client_phone: form.client_phone || null,
        opposing_names: form.opposing.split("\n").map((s) => s.trim()).filter(Boolean),
        summary: form.summary,
        source: form.source,
      });
      setShowNew(false);
      setForm({ client_name: "", client_email: "", client_phone: "", opposing: "", summary: "", source: "referral" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function accept(id: string) {
    const result = await apiPost<Intake>(`/intake/${id}/accept`);
    if (result.matter_id) router.push(`/matters/${result.matter_id}`);
  }

  async function decline(id: string) {
    await apiPost(`/intake/${id}/decline`);
    load();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t.intake}</h1>
        <Button onClick={() => setShowNew(!showNew)}>{t.newIntake}</Button>
      </div>

      <PageIntro k="intake" title={t.intakeIntroT} body={t.intakeIntro} />

      {showNew && (
        <Card className="p-5">
          <form onSubmit={create} className="grid md:grid-cols-3 gap-4">
            <div>
              <Label>{t.clientName}</Label>
              <Input value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} required />
            </div>
            <div>
              <Label>{t.email}</Label>
              <Input type="email" value={form.client_email} onChange={(e) => setForm({ ...form, client_email: e.target.value })} />
            </div>
            <div>
              <Label>{t.phone}</Label>
              <Input value={form.client_phone} onChange={(e) => setForm({ ...form, client_phone: e.target.value })} />
            </div>
            <div>
              <Label>{t.source}</Label>
              <Select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}>
                <option value="referral">{t.referral}</option>
                <option value="web">{t.web}</option>
                <option value="phone">{t.phoneSource}</option>
                <option value="walk_in">{t.walk_in}</option>
                <option value="other">{t.other}</option>
              </Select>
            </div>
            <div className="md:col-span-3">
              <Label>{t.opposingParties}</Label>
              <Textarea rows={2} value={form.opposing} onChange={(e) => setForm({ ...form, opposing: e.target.value })} />
            </div>
            <div className="md:col-span-3">
              <Label>{t.caseSummary}</Label>
              <Textarea rows={4} value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} required />
            </div>
            <div className="md:col-span-3 flex items-center gap-3">
              <Button type="submit" disabled={busy}>{busy ? t.loading : t.save}</Button>
              <Button type="button" variant="secondary" onClick={() => setShowNew(false)}>{t.cancel}</Button>
              <ErrorNote message={error} />
            </div>
          </form>
        </Card>
      )}

      {intakes === null ? (
        <Spinner />
      ) : (
        <div className="space-y-4">
          {intakes.map((intake) => (
            <Card key={intake.id} className="p-5">
              <div className="flex justify-between items-start gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold">{intake.client_name}</h3>
                    <Badge status={intake.status} />
                    {intake.ai_classification?.urgency === "high" && (
                      <Badge status="missed" label={`${t.urgency}: high`} />
                    )}
                  </div>
                  <p className="text-sm text-slate-600 mt-1 line-clamp-2">{intake.summary}</p>

                  {intake.ai_classification && (
                    <div className="mt-2 text-xs text-slate-500">
                      <span className="font-medium">{t.aiClassification}:</span>{" "}
                      {(t as Record<string, string>)[intake.ai_classification.practice_area || ""] ||
                        intake.ai_classification.practice_area}
                      {intake.ai_classification.key_issues && (
                        <> — {intake.ai_classification.key_issues.join("; ")}</>
                      )}
                    </div>
                  )}

                  {intake.conflict_result?.has_conflicts && (
                    <div className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
                      <p className="font-semibold">{t.conflictWarning}</p>
                      {intake.conflict_result.hits
                        .filter((h) => h.appears_in.length > 0)
                        .map((h, i) => (
                          <p key={i}>
                            {h.contact_name}: {h.appears_in.map((a) => `${a.role} @ ${a.matter}`).join(", ")}
                          </p>
                        ))}
                    </div>
                  )}
                </div>

                {(intake.status === "new" || intake.status === "conflict") && (
                  <div className="flex gap-2 shrink-0">
                    <Button onClick={() => accept(intake.id)}>{t.accept}</Button>
                    <Button variant="secondary" onClick={() => decline(intake.id)}>{t.decline}</Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
