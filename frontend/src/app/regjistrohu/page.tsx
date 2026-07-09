"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiPost, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, LocaleSwitcher } from "@/components/ui";

export default function SignupPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [form, setForm] = useState({
    practice_name: "",
    full_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const r = await apiPost<{ access_token: string }>("/auth/signup", {
        ...form,
        locale,
      });
      setToken(r.access_token);
      router.push("/dashboard?welcome=1");
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
          <ErrorNote message={error} />
          <Button type="submit" disabled={busy} className="w-full">
            {t.startTrial}
          </Button>
          <p className="text-xs text-slate-500 text-center">{t.trialTerms}</p>
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
