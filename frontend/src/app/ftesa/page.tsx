"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiPost, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label } from "@/components/ui";

function InviteInner() {
  const { t } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const r = await apiPost<{ access_token: string }>("/auth/accept-invite", {
        token,
        password,
      });
      setToken(r.access_token);
      router.push("/dashboard");
    } catch {
      setError(t.linkInvalid);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="w-full max-w-md p-8 space-y-4">
      <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
      <h2 className="font-semibold">{t.acceptInviteTitle}</h2>
      <p className="text-sm text-slate-500">{t.acceptInviteHint}</p>
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
          {t.joinFirm}
        </Button>
      </form>
    </Card>
  );
}

export default function AcceptInvitePage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50">
      <Suspense fallback={null}>
        <InviteInner />
      </Suspense>
    </div>
  );
}
