"use client";

// Public contact/feedback channel: complaints, suggestions and problem
// reports go straight to the platform operator. No account needed.
import { useState } from "react";
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import { Button, Card, ErrorNote, Input, Label, Textarea } from "@/components/ui";
import { IconCheck, IconMail } from "@/components/icons";

const KINDS = ["ankese", "sugjerim", "problem"] as const;

export default function ContactPage() {
  const { t } = useI18n();
  const [kind, setKind] = useState<(typeof KINDS)[number]>("sugjerim");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const kindLabels: Record<string, string> = {
    ankese: t.ctKindAnkese,
    sugjerim: t.ctKindSugjerim,
    problem: t.ctKindProblem,
  };

  // Count Unicode code points (matches the backend's Python len()), so
  // emoji-heavy messages don't pass client-side and then fail with 422.
  const messageLen = [...message.trim()].length;
  const emailOk = email.trim() === "" || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim());

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!emailOk) {
      setError(t.ctErrEmail);
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/public/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          name: name.trim() || null,
          email: email.trim() || null,
          message: message.trim(),
        }),
      });
      if (!res.ok) {
        if (res.status === 429) throw new Error(t.ctErrRate);
        if (res.status === 422) throw new Error(t.ctErrInvalid);
        throw new Error((await res.json()).detail || t.error);
      }
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <IconMail className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.ctTitle}</h1>
        </div>
        <p className="text-sm text-slate-500">{t.ctIntro}</p>

        {sent ? (
          <Card className="p-8 text-center space-y-3">
            <div className="mx-auto h-12 w-12 rounded-full bg-emerald-50 flex items-center justify-center">
              <IconCheck className="h-6 w-6 text-emerald-600" />
            </div>
            <h2 className="text-lg font-bold text-slate-900">{t.ctSentT}</h2>
            <p className="text-sm text-slate-500">{t.ctSent}</p>
          </Card>
        ) : (
          <Card className="p-5">
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label>{t.ctKind}</Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {KINDS.map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => setKind(k)}
                      className={`rounded-full px-4 py-1.5 text-sm border transition ${
                        kind === k
                          ? "bg-indigo-600 text-white border-indigo-600"
                          : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"
                      }`}
                    >
                      {kindLabels[k]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                <div>
                  <Label>{t.ctName}</Label>
                  <Input value={name} onChange={(e) => setName(e.target.value)} maxLength={120} />
                </div>
                <div>
                  <Label>{t.ctEmail}</Label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    maxLength={255}
                    className={!emailOk ? "!border-red-400" : undefined}
                  />
                  {!emailOk && <p className="text-xs text-red-600 mt-1">{t.ctErrEmail}</p>}
                </div>
              </div>
              <div>
                <Label>{t.ctMessage}</Label>
                <Textarea
                  rows={6}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  required
                  maxLength={5000}
                />
                <p
                  className={`text-xs mt-1 ${
                    messageLen > 0 && messageLen < 10 ? "text-amber-600" : "text-slate-400"
                  }`}
                >
                  {messageLen < 10
                    ? t.ctMsgMore.replace("{n}", String(10 - messageLen))
                    : t.ctMsgOk.replace("{n}", String(messageLen))}
                </p>
              </div>
              <ErrorNote message={error} />
              <Button
                type="submit"
                disabled={busy || messageLen < 10 || !emailOk}
                className="w-full"
              >
                {busy ? t.loading : t.ctSend}
              </Button>
            </form>
          </Card>
        )}
      </main>
    </PublicShell>
  );
}
