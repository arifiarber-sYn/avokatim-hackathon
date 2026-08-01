"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import {
  CitizenInfo,
  citizenGet,
  citizenPost,
  getCitizenToken,
  setCitizenToken,
} from "@/lib/citizen";
import { Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea } from "@/components/ui";
import { clientCountry } from "@/lib/country";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import CitizenAuthForm from "@/components/citizen-auth";
import { IconCheck } from "@/components/icons";

const AREAS = ["civil", "criminal", "family", "commercial", "labor", "administrative", "other"] as const;

function StepIndicator({ current, labels }: { current: number; labels: string[] }) {
  return (
    <ol className="flex items-center gap-2">
      {labels.map((label, i) => {
        const n = i + 1;
        const state = n < current ? "done" : n === current ? "active" : "todo";
        return (
          <li key={label} className="flex items-center gap-2 flex-1 min-w-0">
            <span
              className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                state === "done"
                  ? "bg-emerald-500 text-white"
                  : state === "active"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-200 text-slate-500"
              }`}
            >
              {state === "done" ? <IconCheck className="h-3.5 w-3.5" /> : n}
            </span>
            <span
              className={`text-xs truncate ${
                state === "active" ? "font-semibold text-slate-900" : "text-slate-500"
              }`}
            >
              {label}
            </span>
            {i < labels.length - 1 && <span className="flex-1 h-px bg-slate-200 min-w-2" />}
          </li>
        );
      })}
    </ol>
  );
}

function PostCaseInner() {
  const { t } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const directedTenantId = params.get("avokati");

  const [citizen, setCitizen] = useState<CitizenInfo | null>(null);
  const [checking, setChecking] = useState(true);
  const [form, setForm] = useState({ category: "civil", description: "", city: "", urgency: "normal" });

  // Rechtsschutzversicherung — asked on the German host only (D-037)
  const [isDE, setIsDE] = useState(false);
  useEffect(() => setIsDE(clientCountry() === "DE"), []);
  const [insured, setInsured] = useState<"" | "yes" | "no">("");
  const [insurerName, setInsurerName] = useState("");

  // Prefill from a public Ava conversation ("Më lidh me avokat"): either the
  // structured JSON draft from /ava/structure-case, or a plain-text fallback.
  useEffect(() => {
    const draft = localStorage.getItem("avokatim_case_draft");
    if (!draft) return;
    localStorage.removeItem("avokatim_case_draft");
    try {
      const parsed = JSON.parse(draft);
      if (parsed && typeof parsed === "object" && parsed.description) {
        setForm((f) => ({
          ...f,
          category: typeof parsed.category === "string" ? parsed.category : f.category,
          description: String(parsed.description),
          city: typeof parsed.city === "string" ? parsed.city : f.city,
          urgency: parsed.urgency === "urgent" ? "urgent" : f.urgency,
        }));
        if (typeof parsed.has_legal_insurance === "boolean") {
          setInsured(parsed.has_legal_insurance ? "yes" : "no");
          if (parsed.insurer_name) setInsurerName(String(parsed.insurer_name));
        }
        return;
      }
    } catch {
      // not JSON — legacy plain-text draft
    }
    setForm((f) => ({ ...f, description: draft }));
  }, []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [verifySent, setVerifySent] = useState(false);
  const [posted, setPosted] = useState(false);

  useEffect(() => {
    if (!getCitizenToken()) {
      setChecking(false);
      return;
    }
    citizenGet<CitizenInfo>("/citizen/me")
      .then(setCitizen)
      .catch(() => setCitizenToken(null))
      .finally(() => setChecking(false));
  }, []);

  async function submitCase(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await citizenPost("/citizen/cases", {
        category: form.category,
        description: form.description,
        city: form.city || null,
        urgency: form.urgency,
        directed_tenant_id: directedTenantId,
        has_legal_insurance: insured === "" ? null : insured === "yes",
        insurer_name: insured === "yes" && insurerName ? insurerName : null,
      });
      setPosted(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      setError(status === 403 ? t.mkEmailNotVerified : err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    try {
      await citizenPost("/citizen/resend-verification");
      setVerifySent(true);
    } catch {}
  }

  return (
    <PublicShell>
      <main className="w-full max-w-xl mx-auto px-4 py-8 space-y-4">
        <div>
          <h1 className="text-2xl font-bold">{t.mkPostCase}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.mkPostCaseHint}</p>
        </div>

        <PageIntro k="posto-rastin" title={t.postIntroT} body={t.postIntro} />

        {!checking && (
          <StepIndicator
            current={posted ? 3 : citizen !== null ? 2 : 1}
            labels={[t.psStep1, t.psStep2, t.psStep3]}
          />
        )}

        {checking ? (
          <Spinner />
        ) : posted ? (
          <Card className="p-8 text-center space-y-4">
            <div className="mx-auto h-14 w-14 rounded-full bg-emerald-50 flex items-center justify-center">
              <IconCheck className="h-7 w-7 text-emerald-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">{t.psSuccessT}</h2>
            <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">{t.psSuccess}</p>
            <Button onClick={() => router.push("/rasti-im")} className="w-full sm:w-auto">
              {t.psGoMyCase}
            </Button>
          </Card>
        ) : citizen === null ? (
          <Card className="p-6">
            <CitizenAuthForm
              onAuthed={(c, signedUp) => {
                setCitizen(c);
                if (signedUp) setVerifySent(true);
              }}
            />
          </Card>
        ) : (
          <Card className="p-6 space-y-4">
            {verifySent && (
              <p className="text-sm bg-amber-50 text-amber-800 rounded-lg p-3">{t.mkVerifyEmailSent}</p>
            )}
            {!citizen.email_verified && !verifySent && (
              <p className="text-sm bg-amber-50 text-amber-800 rounded-lg p-3">
                {t.mkEmailNotVerified}{" "}
                <button onClick={resend} className="text-indigo-600 font-medium hover:underline">
                  {t.mkResendVerification}
                </button>
              </p>
            )}
            <form onSubmit={submitCase} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>{t.mkCategory}</Label>
                  <Select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                  >
                    {AREAS.map((a) => (
                      <option key={a} value={a}>{t[a]}</option>
                    ))}
                  </Select>
                </div>
                <div>
                  <Label>{t.mkUrgency}</Label>
                  <Select
                    value={form.urgency}
                    onChange={(e) => setForm({ ...form, urgency: e.target.value })}
                  >
                    <option value="normal">{t.mkNormal}</option>
                    <option value="urgent">{t.mkUrgent}</option>
                  </Select>
                </div>
              </div>
              <div>
                <Label>{t.mkCity}</Label>
                <Input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
              </div>
              <div>
                <Label>{t.mkDescribeCase}</Label>
                <Textarea
                  rows={6}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  required
                  minLength={20}
                />
              </div>
              {isDE && (
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-2">
                  <Label>{t.rsvQuestion}</Label>
                  <div className="flex gap-4">
                    {(["yes", "no"] as const).map((value) => (
                      <label key={value} className="flex items-center gap-1.5 text-sm text-slate-700">
                        <input
                          type="radio"
                          name="rsv"
                          checked={insured === value}
                          onChange={() => setInsured(value)}
                        />
                        {value === "yes" ? t.rsvYes : t.rsvNo}
                      </label>
                    ))}
                  </div>
                  {insured === "yes" && (
                    <div>
                      <Label>{t.rsvInsurer}</Label>
                      <Input
                        value={insurerName}
                        onChange={(e) => setInsurerName(e.target.value)}
                        placeholder="ARAG, Allianz, …"
                        maxLength={120}
                      />
                    </div>
                  )}
                  <p className="text-xs text-slate-400">{t.rsvHint}</p>
                </div>
              )}
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy} className="w-full">
                {busy ? t.loading : t.mkPostCase}
              </Button>
            </form>
          </Card>
        )}
        <p className="text-xs text-slate-400 text-center">{t.mkDisclaimer}</p>
      </main>
    </PublicShell>
  );
}

export default function PostCasePage() {
  return (
    <Suspense fallback={<Spinner />}>
      <PostCaseInner />
    </Suspense>
  );
}
