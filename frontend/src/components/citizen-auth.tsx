"use client";

/**
 * Shared citizen signup/login form (used by /kycu and /posto-rastin).
 * Includes the forgot-password flow; the reset-with-token form lives in /kycu.
 */
import { useState } from "react";
import { useI18n } from "@/lib/i18n";
import { CitizenInfo, citizenPost, setCitizenToken } from "@/lib/citizen";
import { Button, ErrorNote, Input, Label } from "@/components/ui";

type Mode = "signup" | "login" | "forgot";

export default function CitizenAuthForm({
  onAuthed,
  defaultMode = "signup",
}: {
  onAuthed: (citizen: CitizenInfo, signedUp: boolean) => void;
  defaultMode?: "signup" | "login";
}) {
  const { t, locale } = useI18n();
  const [mode, setMode] = useState<Mode>(defaultMode);
  const [auth, setAuth] = useState({ full_name: "", email: "", phone: "", password: "" });
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [resetSent, setResetSent] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "forgot") {
        await citizenPost("/citizen/forgot-password", { email: auth.email });
        setResetSent(true);
        return;
      }
      const path = mode === "signup" ? "/citizen/signup" : "/citizen/login";
      const body =
        mode === "signup"
          ? { ...auth, phone: auth.phone || null, locale, accept_privacy: acceptPrivacy }
          : { email: auth.email, password: auth.password };
      const data = await citizenPost<{ access_token: string; citizen: CitizenInfo }>(path, body);
      setCitizenToken(data.access_token);
      onAuthed(data.citizen, mode === "signup");
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  if (mode === "forgot" && resetSent) {
    return (
      <div className="space-y-4">
        <p className="text-sm bg-emerald-50 text-emerald-800 rounded-lg p-3">{t.acctResetSent}</p>
        <button
          className="text-sm text-indigo-600 hover:underline"
          onClick={() => {
            setMode("login");
            setResetSent(false);
          }}
        >
          {t.login}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {mode !== "forgot" && (
        <div className="flex gap-2 text-sm">
          <button
            className={`flex-1 rounded-lg py-2 font-medium ${mode === "signup" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}
            onClick={() => setMode("signup")}
            type="button"
          >
            {t.mkSignup}
          </button>
          <button
            className={`flex-1 rounded-lg py-2 font-medium ${mode === "login" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}
            onClick={() => setMode("login")}
            type="button"
          >
            {t.login}
          </button>
        </div>
      )}
      {mode === "forgot" && <h2 className="font-semibold">{t.acctForgot}</h2>}

      <form onSubmit={submit} className="space-y-4">
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
        {mode !== "forgot" && (
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
        )}
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
          {busy
            ? t.loading
            : mode === "signup"
              ? t.mkSignup
              : mode === "login"
                ? t.login
                : t.acctForgot}
        </Button>
      </form>

      {mode === "login" && (
        <button
          className="text-xs text-slate-500 hover:text-indigo-600 hover:underline"
          onClick={() => setMode("forgot")}
          type="button"
        >
          {t.acctForgot}
        </button>
      )}
      {mode === "forgot" && (
        <button
          className="text-xs text-slate-500 hover:text-indigo-600 hover:underline"
          onClick={() => setMode("login")}
          type="button"
        >
          {t.login}
        </button>
      )}
    </div>
  );
}
