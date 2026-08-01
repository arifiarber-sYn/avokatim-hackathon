"use client";

/**
 * Citizen sign-in page — the citizen counterpart of the lawyer /login.
 * Also hosts the password-reset form (?rivendos=<token> from the email link).
 */
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { CitizenInfo, citizenGet, citizenPost, getCitizenToken } from "@/lib/citizen";
import { Button, Card, ErrorNote, Input, Label, Spinner } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import CitizenAuthForm from "@/components/citizen-auth";
import { IconCheck } from "@/components/icons";

function ResetForm({ token }: { token: string }) {
  const { t } = useI18n();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await citizenPost("/citizen/reset-password", { token, new_password: password });
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="text-center space-y-4">
        <div className="mx-auto h-14 w-14 rounded-full bg-emerald-50 flex items-center justify-center">
          <IconCheck className="h-7 w-7 text-emerald-600" />
        </div>
        <p className="text-sm text-slate-600">{t.acctResetDone}</p>
        <Link href="/kycu" className="text-sm font-semibold text-indigo-600 hover:underline">
          {t.login}
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h2 className="font-semibold">{t.acctResetT}</h2>
      <div>
        <Label>{t.acctPwNew}</Label>
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
        />
      </div>
      <ErrorNote message={error} />
      <Button type="submit" disabled={busy} className="w-full">
        {busy ? t.loading : t.acctResetT}
      </Button>
    </form>
  );
}

function CitizenLoginInner() {
  const { t } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const resetToken = params.get("rivendos");
  const [checking, setChecking] = useState(true);

  // Already signed in? Go straight to the account page.
  useEffect(() => {
    if (resetToken || !getCitizenToken()) {
      setChecking(false);
      return;
    }
    citizenGet<CitizenInfo>("/citizen/me")
      .then(() => router.replace("/llogaria"))
      .catch(() => setChecking(false));
  }, [router, resetToken]);

  return (
    <PublicShell>
      <main className="w-full max-w-md mx-auto px-4 py-10 space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold">{t.acctLoginT}</h1>
        </div>
        {checking ? (
          <Spinner />
        ) : (
          <Card className="p-6">
            {resetToken ? (
              <ResetForm token={resetToken} />
            ) : (
              <CitizenAuthForm defaultMode="login" onAuthed={() => router.push("/llogaria")} />
            )}
          </Card>
        )}
        <p className="text-center text-xs text-slate-400">
          <Link href="/login" className="inline-block py-1.5 hover:text-indigo-600 hover:underline">
            {t.acctIsLawyer}
          </Link>
        </p>
      </main>
    </PublicShell>
  );
}

export default function CitizenLoginPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <CitizenLoginInner />
    </Suspense>
  );
}
