"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiPost, setToken } from "@/lib/api";
import { clientCountry, fmtPricing } from "@/lib/country";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, LocaleSwitcher } from "@/components/ui";

export default function SignupPage() {
  return (
    <Suspense>
      <SignupInner />
    </Suspense>
  );
}

function SignupInner() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();
  // Lawyer-brings-lawyer program: ?ref=<code> from a colleague's share link
  const referralCode = searchParams.get("ref");
  const [form, setForm] = useState({
    practice_name: "",
    full_name: "",
    email: "",
    password: "",
  });
  // /per-noteret links here with ?profesioni=noter to preselect the notary card
  const [profession, setProfession] = useState<"lawyer" | "notary">(
    searchParams.get("profesioni") === "noter" ? "notary" : "lawyer"
  );
  const [acceptTos, setAcceptTos] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  // The notary pillar is Kosovo-only in v1 (D-034)
  const [isDE, setIsDE] = useState(false);
  useEffect(() => {
    if (clientCountry() === "DE") {
      setIsDE(true);
      setProfession("lawyer");
    }
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const r = await apiPost<{ access_token: string }>("/auth/signup", {
        ...form,
        locale,
        profession,
        accept_tos: acceptTos,
        referral_code: referralCode,
      });
      setToken(r.access_token);
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50">
      <Card className="w-full max-w-md p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
            <p className="text-sm text-slate-500">{t.signupSubtitle}</p>
          </div>
          <LocaleSwitcher />
        </div>
        <form onSubmit={submit} className="space-y-4">
          {!isDE && (
          <div>
            <Label>{t.signupProfession}</Label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              {(
                [
                  { key: "lawyer", label: t.signupProfLawyer, hint: t.signupProfLawyerHint },
                  { key: "notary", label: t.signupProfNotary, hint: t.signupProfNotaryHint },
                ] as const
              ).map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setProfession(opt.key)}
                  className={`rounded-xl border p-3 text-left transition ${
                    profession === opt.key
                      ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <span className="block text-sm font-semibold text-slate-800">{opt.label}</span>
                  <span className="block text-xs text-slate-500 mt-0.5">{opt.hint}</span>
                </button>
              ))}
            </div>
          </div>
          )}
          <div>
            <Label>{t.practiceName}</Label>
            <Input
              value={form.practice_name}
              onChange={(e) => setForm({ ...form, practice_name: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>{t.fullName}</Label>
            <Input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>{t.email}</Label>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>{t.password}</Label>
            <Input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              minLength={10}
            />
            <p className="text-xs text-slate-400 mt-1">{t.passwordMinHint}</p>
          </div>
          <label className="flex items-start gap-2 text-xs text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={acceptTos}
              onChange={(e) => setAcceptTos(e.target.checked)}
              required
              className="mt-0.5 accent-indigo-600"
            />
            <span>
              {t.acceptTosLabel} —{" "}
              <Link href="/kushtet" target="_blank" className="text-indigo-600 hover:underline">
                {t.termsOfService}
              </Link>
              {" · "}
              <Link href="/privatesia" target="_blank" className="text-indigo-600 hover:underline">
                {t.privacyPolicy}
              </Link>
            </span>
          </label>
          <ErrorNote message={error} />
          <Button type="submit" disabled={busy || !acceptTos} className="w-full">
            {fmtPricing(t.startTrial, isDE ? "DE" : "XK")}
          </Button>
          <p className="text-xs text-slate-500 text-center">
            {fmtPricing(t.trialTerms, isDE ? "DE" : "XK")}
          </p>
        </form>
        <p className="text-sm text-slate-500 mt-6 text-center">
          {t.alreadyHaveAccount}{" "}
          <Link href="/login" className="text-indigo-600 hover:underline">
            {t.login}
          </Link>
        </p>
      </Card>
    </div>
  );
}
