"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiGet, apiPost, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, LocaleSwitcher } from "@/components/ui";

type Mode = "login" | "setup" | "2fa";

interface TokenResponse {
  access_token: string;
  requires_2fa: boolean;
}

export default function LoginPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [practiceName, setPracticeName] = useState("");
  const [code, setCode] = useState("");
  const [preToken, setPreToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiGet<{ setup_needed: boolean }>("/auth/setup-needed")
      .then((r) => setMode(r.setup_needed ? "setup" : "login"))
      .catch(() => {});
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "setup") {
        const r = await apiPost<TokenResponse>("/auth/register", {
          practice_name: practiceName,
          full_name: fullName,
          email,
          password,
        });
        setToken(r.access_token);
        router.push("/dashboard");
      } else if (mode === "login") {
        const r = await apiPost<TokenResponse>("/auth/login", { email, password });
        if (r.requires_2fa) {
          setPreToken(r.access_token);
          setMode("2fa");
        } else {
          setToken(r.access_token);
          router.push("/dashboard");
        }
      } else {
        const res = await fetch(`/api/auth/2fa/verify`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${preToken}`,
          },
          body: JSON.stringify({ code }),
        });
        if (!res.ok) throw new Error(t.invalidCredentials);
        const r = (await res.json()) as TokenResponse;
        setToken(r.access_token);
        router.push("/dashboard");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t.invalidCredentials);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50">
      <div className="w-full max-w-md mb-3 text-center">
        <Link
          href="/kycu"
          className="inline-block text-xs text-slate-500 bg-white/70 border border-slate-200 rounded-full px-4 py-1.5 hover:text-indigo-700 hover:border-indigo-200"
        >
          {t.acctIsCitizen}
        </Link>
      </div>
      <Card className="w-full max-w-md p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
            <p className="text-sm text-slate-500">{t.tagline}</p>
          </div>
          <LocaleSwitcher />
        </div>

        {mode === "setup" && (
          <div className="mb-4">
            <h2 className="text-lg font-semibold">{t.firstRunTitle}</h2>
            <p className="text-sm text-slate-500">{t.firstRunSubtitle}</p>
          </div>
        )}

        <form onSubmit={submit} className="space-y-4">
          {mode === "setup" && (
            <>
              <div>
                <Label>{t.practiceName}</Label>
                <Input value={practiceName} onChange={(e) => setPracticeName(e.target.value)} required />
              </div>
              <div>
                <Label>{t.fullName}</Label>
                <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
              </div>
            </>
          )}

          {mode !== "2fa" && (
            <>
              <div>
                <Label>{t.email}</Label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div>
                <Label>{t.password}</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={mode === "setup" ? 10 : undefined}
                />
              </div>
            </>
          )}

          {mode === "2fa" && (
            <div>
              <Label>{t.twoFACode}</Label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                autoFocus
                inputMode="numeric"
                maxLength={8}
                required
              />
            </div>
          )}

          <ErrorNote message={error} />

          <Button type="submit" disabled={busy} className="w-full">
            {mode === "setup" ? t.createAccount : mode === "2fa" ? t.verify : t.login}
          </Button>
        </form>

        {mode === "login" && (
          <div className="mt-6 space-y-2 text-center text-sm">
            <p>
              <Link href="/harrova-fjalekalimin" className="text-slate-500 hover:text-indigo-600 hover:underline">
                {t.forgotPasswordTitle}
              </Link>
            </p>
            <p className="text-slate-500">
              {t.noAccountYet}{" "}
              <Link href="/regjistrohu" className="text-indigo-600 hover:underline">
                {t.startTrial}
              </Link>
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
