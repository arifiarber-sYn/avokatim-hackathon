"use client";

import { use, useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, LocaleSwitcher, Spinner, Textarea } from "@/components/ui";

export default function PublicIntakePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const { t } = useI18n();
  const [practiceName, setPracticeName] = useState<string | null>(null);
  const [logo, setLogo] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [form, setForm] = useState({ client_name: "", client_email: "", client_phone: "", summary: "" });
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`/api/public/intake/${token}`)
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((data) => {
        setPracticeName(data.practice_name);
        setLogo(data.logo || null);
      })
      .catch(() => setNotFound(true));
  }, [token]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`/api/public/intake/${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_name: form.client_name,
          client_email: form.client_email || null,
          client_phone: form.client_phone || null,
          summary: form.summary,
          accept_privacy: acceptPrivacy,
        }),
      });
      if (!res.ok) throw new Error(t.error);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            {logo && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={logo} alt="" className="h-8 w-8 rounded object-contain" />
            )}
            <h1 className="text-lg font-bold text-indigo-700 truncate">{practiceName || "BoraLaw"}</h1>
          </div>
          <LocaleSwitcher />
        </div>
      </header>
      <main className="max-w-xl mx-auto px-4 py-10">
        {notFound ? (
          <Card className="p-6">
            <p className="text-sm text-slate-600">{t.formNotFound}</p>
          </Card>
        ) : practiceName === null ? (
          <Spinner />
        ) : sent ? (
          <Card className="p-8 text-center space-y-2">
            <p className="text-3xl">✓</p>
            <p className="font-medium">{t.applicationReceived}</p>
          </Card>
        ) : (
          <Card className="p-6 space-y-5">
            <div>
              <h2 className="font-bold text-lg">{t.applyTitle}</h2>
              <p className="text-sm text-slate-500">{t.applySubtitle}</p>
            </div>
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label>{t.yourName}</Label>
                <Input
                  value={form.client_name}
                  onChange={(e) => setForm({ ...form, client_name: e.target.value })}
                  required
                  minLength={2}
                />
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>{t.yourEmail}</Label>
                  <Input
                    type="email"
                    value={form.client_email}
                    onChange={(e) => setForm({ ...form, client_email: e.target.value })}
                  />
                </div>
                <div>
                  <Label>{t.yourPhone}</Label>
                  <Input
                    value={form.client_phone}
                    onChange={(e) => setForm({ ...form, client_phone: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <Label>{t.describeYourCase}</Label>
                <Textarea
                  rows={6}
                  value={form.summary}
                  onChange={(e) => setForm({ ...form, summary: e.target.value })}
                  required
                  minLength={10}
                />
              </div>
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
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy || !acceptPrivacy} className="w-full">
                {busy ? t.loading : t.submitApplication}
              </Button>
            </form>
          </Card>
        )}
      </main>
    </div>
  );
}
