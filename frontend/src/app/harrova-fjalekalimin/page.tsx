"use client";

import { useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label } from "@/components/ui";

export default function ForgotPasswordPage() {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await apiPost("/auth/forgot-password", { email });
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50">
      <Card className="w-full max-w-md p-8 space-y-4">
        <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
        <h2 className="font-semibold">{t.forgotPasswordTitle}</h2>
        {sent ? (
          <p className="text-sm text-emerald-700">✓ {t.resetEmailSent}</p>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <p className="text-sm text-slate-500">{t.forgotPasswordHint}</p>
            <div>
              <Label>{t.email}</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <ErrorNote message={error} />
            <Button type="submit" disabled={busy} className="w-full">
              {t.sendResetLink}
            </Button>
          </form>
        )}
        <p className="text-sm text-slate-500 text-center">
          <Link href="/login" className="text-indigo-600 hover:underline">
            {t.backToLogin}
          </Link>
        </p>
      </Card>
    </div>
  );
}
