"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label } from "@/components/ui";

function ResetInner() {
  const { t } = useI18n();
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await apiPost("/auth/reset-password", { token, password });
      setDone(true);
    } catch {
      setError(t.linkInvalid);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="w-full max-w-md p-8 space-y-4">
      <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
      <h2 className="font-semibold">{t.resetPasswordTitle}</h2>
      {done ? (
        <>
          <p className="text-sm text-emerald-700">✓ {t.passwordResetDone}</p>
          <Link href="/login" className="text-indigo-600 hover:underline text-sm">
            {t.login}
          </Link>
        </>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div>
            <Label>{t.newPassword}</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={10}
            />
            <p className="text-xs text-slate-400 mt-1">{t.passwordMinHint}</p>
          </div>
          <ErrorNote message={error} />
          <Button type="submit" disabled={busy} className="w-full">
            {t.resetPasswordTitle}
          </Button>
        </form>
      )}
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50">
      <Suspense fallback={null}>
        <ResetInner />
      </Suspense>
    </div>
  );
}
