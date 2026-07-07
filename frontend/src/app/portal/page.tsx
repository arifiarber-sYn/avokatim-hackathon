"use client";

import { useCallback, useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, LocaleSwitcher, Spinner } from "@/components/ui";

const TOKEN_KEY = "boralaw_portal_token";
const NAME_KEY = "boralaw_portal_name";
const API = "/api/portal";

function portalToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

async function portalApi<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  const token = portalToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    window.location.reload();
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

interface PortalMatter {
  id: string;
  reference: string;
  title: string;
  status: string;
  court_name: string | null;
  upcoming_hearings: { title: string; at: string }[];
}

interface PortalMsg {
  id: string;
  from_client: boolean;
  body: string;
  created_at: string;
}

interface PortalSig {
  id: string;
  document_name: string;
  status: string;
  note: string | null;
  requested_at: string;
  signed_at: string | null;
}

export default function PortalPage() {
  const { t } = useI18n();
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [clientName, setClientName] = useState("");

  useEffect(() => {
    setAuthed(!!portalToken());
    setClientName(localStorage.getItem(NAME_KEY) || "");
  }, []);

  if (authed === null) return <Spinner />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-indigo-700">BoraLaw</h1>
            <p className="text-xs text-slate-500">{t.portalTitle}</p>
          </div>
          <div className="flex items-center gap-4">
            <LocaleSwitcher />
            {authed && (
              <button
                onClick={() => {
                  localStorage.removeItem(TOKEN_KEY);
                  localStorage.removeItem(NAME_KEY);
                  setAuthed(false);
                }}
                className="text-sm text-slate-500 hover:text-slate-800"
              >
                {t.logout}
              </button>
            )}
          </div>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-4 py-8">
        {authed ? (
          <PortalHome clientName={clientName} />
        ) : (
          <PortalLogin
            onLogin={(name) => {
              setClientName(name);
              setAuthed(true);
            }}
          />
        )}
      </main>
    </div>
  );
}

function PortalLogin({ onLogin }: { onLogin: (name: string) => void }) {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error(t.invalidCredentials);
      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(NAME_KEY, data.client_name);
      onLogin(data.client_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-12">
      <Card className="p-6 space-y-4">
        <div>
          <h2 className="font-bold text-lg">{t.portalLogin}</h2>
          <p className="text-sm text-slate-500">{t.portalSubtitle}</p>
        </div>
        <form onSubmit={login} className="space-y-3">
          <div>
            <Label>{t.email}</Label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <Label>{t.password}</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <ErrorNote message={error} />
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? t.loading : t.login}
          </Button>
        </form>
      </Card>
    </div>
  );
}

function PortalHome({ clientName }: { clientName: string }) {
  const { t } = useI18n();
  const [matters, setMatters] = useState<PortalMatter[] | null>(null);
  const [sigs, setSigs] = useState<PortalSig[]>([]);
  const [openMatter, setOpenMatter] = useState<PortalMatter | null>(null);

  const load = useCallback(() => {
    portalApi<PortalMatter[]>("/my-matters").then(setMatters).catch(() => {});
    portalApi<PortalSig[]>("/signatures").then(setSigs).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (matters === null) return <Spinner />;

  if (openMatter) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setOpenMatter(null)}
          className="text-sm text-indigo-600 hover:underline"
        >
          ← {t.backToMatters}
        </button>
        <h2 className="font-bold text-lg">
          {openMatter.title} <span className="text-sm font-mono text-slate-400">{openMatter.reference}</span>
        </h2>
        <PortalMessages matterId={openMatter.id} />
      </div>
    );
  }

  const pendingSigs = sigs.filter((s) => s.status === "pending");

  return (
    <div className="space-y-6">
      <h2 className="font-bold text-xl">{clientName}</h2>

      {pendingSigs.length > 0 && (
        <section className="space-y-3">
          <h3 className="font-semibold text-sm text-amber-700">
            ✍ {t.documentsToSign} ({pendingSigs.length})
          </h3>
          {pendingSigs.map((s) => (
            <SignCard key={s.id} sig={s} onDone={load} />
          ))}
        </section>
      )}

      <section className="space-y-3">
        <h3 className="font-semibold text-sm text-slate-600">{t.myMatters}</h3>
        {matters.map((m) => (
          <Card key={m.id} className="p-4 hover:border-indigo-300 transition-colors">
            <button className="w-full text-left" onClick={() => setOpenMatter(m)}>
              <div className="flex justify-between items-start gap-3">
                <div>
                  <p className="font-medium">{m.title}</p>
                  <p className="text-xs text-slate-500 font-mono">{m.reference}</p>
                  {m.court_name && <p className="text-xs text-slate-500 mt-1">{m.court_name}</p>}
                </div>
                <span className="text-xs text-indigo-600">{t.messages} →</span>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100">
                <p className="text-xs font-medium text-slate-500 mb-1">{t.upcomingHearings}</p>
                {m.upcoming_hearings.length === 0 ? (
                  <p className="text-xs text-slate-400">{t.noHearings}</p>
                ) : (
                  m.upcoming_hearings.map((h, i) => (
                    <p key={i} className="text-xs text-slate-600">
                      • {h.title} — {new Date(h.at).toLocaleString()}
                    </p>
                  ))
                )}
              </div>
            </button>
          </Card>
        ))}
      </section>
    </div>
  );
}

function SignCard({ sig, onDone }: { sig: PortalSig; onDone: () => void }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function sign(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await portalApi(`/signatures/${sig.id}/sign`, {
        method: "POST",
        body: JSON.stringify({ signer_name: name }),
      });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function decline() {
    setBusy(true);
    try {
      await portalApi(`/signatures/${sig.id}/decline`, { method: "POST" });
      onDone();
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-4 border-amber-200 bg-amber-50/40 space-y-3">
      <div className="flex justify-between items-center gap-3">
        <div>
          <p className="font-medium text-sm">{sig.document_name}</p>
          {sig.note && <p className="text-xs text-slate-500 mt-0.5">{sig.note}</p>}
        </div>
        {!open && <Button onClick={() => setOpen(true)}>{t.signDocument}</Button>}
      </div>
      {open && (
        <form onSubmit={sign} className="space-y-3 pt-2 border-t border-amber-100">
          <p className="text-xs text-slate-600">{t.typeNameToSign}</p>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t.yourName}
            required
            minLength={3}
          />
          <ErrorNote message={error} />
          <div className="flex gap-2">
            <Button type="submit" disabled={busy || name.trim().length < 3}>
              {t.signNow}
            </Button>
            <Button type="button" variant="secondary" onClick={decline} disabled={busy}>
              {t.declineBtn}
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}

function PortalMessages({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<PortalMsg[]>([]);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    portalApi<PortalMsg[]>(`/matters/${matterId}/messages`).then(setMessages).catch(() => {});
  }, [matterId]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, [load]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    try {
      await portalApi(`/matters/${matterId}/messages`, {
        method: "POST",
        body: JSON.stringify({ body }),
      });
      setBody("");
      load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="p-4 space-y-3 max-h-[26rem] overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-6">{t.noMessages}</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.from_client ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
                m.from_client ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.body}</p>
              <p className={`text-[10px] mt-1 ${m.from_client ? "text-indigo-200" : "text-slate-400"}`}>
                {new Date(m.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </Card>
      <form onSubmit={send} className="flex gap-2">
        <Input
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder={t.writeMessageClient}
          className="flex-1"
        />
        <Button type="submit" disabled={busy || !body.trim()}>{t.send}</Button>
      </form>
    </div>
  );
}
