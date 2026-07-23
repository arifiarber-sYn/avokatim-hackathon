"use client";

/**
 * Shared citizen signup/login form (used by /kycu and /posto-rastin).
 * Social login first (Google / Apple / Meta — what users asked for), email
 * as the fallback. Includes the forgot-password flow; the reset-with-token
 * form lives in /kycu.
 */
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { CitizenInfo, citizenGet, citizenPost, setCitizenToken } from "@/lib/citizen";
import { Button, ErrorNote, Input, Label } from "@/components/ui";

type Mode = "signup" | "login" | "forgot";

const PROVIDER_LABEL: Record<string, string> = {
  google: "Google",
  apple: "Apple",
  meta: "Facebook",
};

function ProviderIcon({ provider }: { provider: string }) {
  if (provider === "google")
    return (
      <svg viewBox="0 0 24 24" className="w-5 h-5" aria-hidden>
        <path fill="#4285F4" d="M23.5 12.3c0-.9-.1-1.5-.3-2.3H12v4.5h6.5c-.1 1.1-.8 2.7-2.4 3.8l3.7 2.9c2.3-2.1 3.7-5.2 3.7-8.9z" />
        <path fill="#34A853" d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-3.7-2.9c-1 .7-2.4 1.2-4.2 1.2-3.1 0-5.8-2.1-6.8-5l-3.9 3C3.3 21.3 7.3 24 12 24z" />
        <path fill="#FBBC05" d="M5.2 14.4c-.2-.7-.4-1.5-.4-2.4s.2-1.7.4-2.4l-3.9-3C.5 8.2 0 10 0 12s.5 3.8 1.3 5.4l3.9-3z" />
        <path fill="#EA4335" d="M12 4.6c1.8 0 3 .8 3.7 1.4l3.3-3.2C17.8 1 15.2 0 12 0 7.3 0 3.3 2.7 1.3 6.6l3.9 3c1-2.9 3.7-5 6.8-5z" />
      </svg>
    );
  if (provider === "apple")
    return (
      <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current" aria-hidden>
        <path d="M16.7 12.9c0-2.4 2-3.6 2.1-3.7-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.8-1.6 0-3.1 1-4 2.4-1.7 3-.4 7.4 1.2 9.8.8 1.2 1.8 2.5 3.1 2.4 1.2-.1 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9zM14.4 5.2c.7-.8 1.1-1.9 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z" />
      </svg>
    );
  return (
    <svg viewBox="0 0 24 24" className="w-5 h-5" aria-hidden>
      <path fill="#1877F2" d="M24 12a12 12 0 1 0-13.9 11.9v-8.4h-3V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.3l-.5 3.5h-2.8v8.4A12 12 0 0 0 24 12z" />
    </svg>
  );
}

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
  const [providers, setProviders] = useState<string[]>([]);

  // Social login: which buttons to show + catch the token/error the backend
  // put in the URL fragment after the OAuth callback
  useEffect(() => {
    citizenGet<{ providers: string[] }>("/oauth/providers")
      .then((d) => setProviders(d.providers))
      .catch(() => {});
    const hash = new URLSearchParams(window.location.hash.slice(1));
    const token = hash.get("citizen_token");
    const oauthError = hash.get("oauth_error");
    if (token || oauthError) {
      history.replaceState(null, "", window.location.pathname + window.location.search);
    }
    if (token) {
      setCitizenToken(token);
      citizenGet<CitizenInfo>("/citizen/me")
        .then((citizen) => onAuthed(citizen, false))
        .catch(() => setCitizenToken(null));
    } else if (oauthError) {
      setError(oauthError === "no_email" ? t.authOauthNoEmail : t.authOauthError);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function startOauth(provider: string) {
    const next = encodeURIComponent(window.location.pathname);
    window.location.href = `/api/public/oauth/${provider}/start?locale=${locale}&next=${next}`;
  }

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

      {mode !== "forgot" && providers.length > 0 && (
        <div className="space-y-2">
          {providers.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => startOauth(p)}
              className={`w-full flex items-center justify-center gap-2.5 rounded-lg border py-2.5 text-sm font-medium transition-colors ${
                p === "apple"
                  ? "bg-black text-white border-black hover:bg-slate-800"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
              }`}
            >
              <ProviderIcon provider={p} />
              {t.authContinueWith} {PROVIDER_LABEL[p]}
            </button>
          ))}
          <p className="text-[11px] text-slate-400 text-center">{t.authOauthPrivacy}</p>
          <div className="flex items-center gap-3 pt-1">
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-xs text-slate-400">{t.authOrEmail}</span>
            <div className="flex-1 h-px bg-slate-200" />
          </div>
        </div>
      )}

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
