"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
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
import PublicShell from "@/components/public-shell";

const AREAS = ["civil", "criminal", "family", "commercial", "labor", "administrative", "other"] as const;

function PostCaseInner() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const directedTenantId = params.get("avokati");

  const [citizen, setCitizen] = useState<CitizenInfo | null>(null);
  const [checking, setChecking] = useState(true);
  const [mode, setMode] = useState<"signup" | "login">("signup");
  const [auth, setAuth] = useState({ full_name: "", email: "", phone: "", password: "" });
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [form, setForm] = useState({ category: "civil", description: "", city: "", urgency: "normal" });

  // Prefill from a public Ava conversation ("Më lidh me avokat")
  useEffect(() => {
    const draft = localStorage.getItem("avokatim_case_draft");
    if (draft) {
      setForm((f) => ({ ...f, description: draft }));
      localStorage.removeItem("avokatim_case_draft");
    }
  }, []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [verifySent, setVerifySent] = useState(false);

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

  async function doAuth(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const path = mode === "signup" ? "/citizen/signup" : "/citizen/login";
      const body =
        mode === "signup"
          ? { ...auth, phone: auth.phone || null, locale, accept_privacy: acceptPrivacy }
          : { email: auth.email, password: auth.password };
      const data = await citizenPost<{ access_token: string; citizen: CitizenInfo }>(path, body);
      setCitizenToken(data.access_token);
      setCitizen(data.citizen);
      if (mode === "signup") setVerifySent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

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
      });
      router.push("/rasti-im");
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

        {checking ? (
          <Spinner />
        ) : citizen === null ? (
          <Card className="p-6 space-y-4">
            <div className="flex gap-2 text-sm">
              <button
                className={`flex-1 rounded-lg py-2 font-medium ${mode === "signup" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}
                onClick={() => setMode("signup")}
              >
                {t.mkSignup}
              </button>
              <button
                className={`flex-1 rounded-lg py-2 font-medium ${mode === "login" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}
                onClick={() => setMode("login")}
              >
                {t.login}
              </button>
            </div>
            <form onSubmit={doAuth} className="space-y-4">
              {mode === "signup" && (
                <div>
                  <Label>{t.fullName}</Label>
                  <Input
                    value={auth.full_name}
                    onChange={(e) => setAuth({ ...auth, full_name: e.target.value })}
                    required
                    minLength={2}
                  />
                </div>
              )}
              <div>
                <Label>{t.email}</Label>
                <Input
                  type="email"
                  value={auth.email}
                  onChange={(e) => setAuth({ ...auth, email: e.target.value })}
                  required
                />
              </div>
              {mode === "signup" && (
                <div>
                  <Label>{t.mkPhone}</Label>
                  <Input value={auth.phone} onChange={(e) => setAuth({ ...auth, phone: e.target.value })} />
                </div>
              )}
              <div>
                <Label>{t.password}</Label>
                <Input
                  type="password"
                  value={auth.password}
                  onChange={(e) => setAuth({ ...auth, password: e.target.value })}
                  required
                  minLength={8}
                />
              </div>
              {mode === "signup" && (
                <label className="flex items-start gap-2 text-xs text-slate-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={acceptPrivacy}
                    onChange={(e) => setAcceptPrivacy(e.target.checked)}
                    required
                    className="mt-0.5 accent-indigo-600"
                  />
                  <span>
                    {t.acceptPrivacyIntake} —{" "}
                    <a href="/privatesia" target="_blank" className="text-indigo-600 hover:underline">
                      {t.privacyPolicy}
                    </a>
                  </span>
                </label>
              )}
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy} className="w-full">
                {busy ? t.loading : mode === "signup" ? t.mkSignup : t.login}
              </Button>
            </form>
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
