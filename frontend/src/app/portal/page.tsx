"use client";

import { useCallback, useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { Button, Card, ErrorNote, Input, Label, LocaleSwitcher, Spinner } from "@/components/ui";
import Brand from "@/components/brand";

const TOKEN_KEY = "avokatim_portal_token";
const NAME_KEY = "avokatim_portal_name";
const FIRM_NAME_KEY = "avokatim_portal_firm";
const FIRM_LOGO_KEY = "avokatim_portal_firm_logo";
const TERMS_KEY = "avokatim_portal_terms";
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

interface PortalDoc {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  category: string | null;
  created_at: string;
}

export default function PortalPage() {
  const { t } = useI18n();
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [termsOk, setTermsOk] = useState(true);
  const [clientName, setClientName] = useState("");
  const [firmName, setFirmName] = useState("");
  const [firmLogo, setFirmLogo] = useState("");

  useEffect(() => {
    setAuthed(!!portalToken());
    setTermsOk(localStorage.getItem(TERMS_KEY) !== "pending");
    setClientName(localStorage.getItem(NAME_KEY) || "");
    setFirmName(localStorage.getItem(FIRM_NAME_KEY) || "");
    setFirmLogo(localStorage.getItem(FIRM_LOGO_KEY) || "");
  }, []);

  if (authed === null) return <Spinner />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            {firmLogo && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={firmLogo} alt="" className="h-8 w-8 rounded object-contain shrink-0" />
            )}
            <div className="min-w-0">
              <h1 className="text-lg font-bold text-indigo-700 truncate">{firmName || <Brand />}</h1>
              <p className="text-xs text-slate-500 truncate">{t.portalTitle}</p>
            </div>
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
      <main className="max-w-3xl mx-auto px-4 py-5 sm:py-8">
        {authed && !termsOk ? (
          <PortalAcceptTerms onAccepted={() => setTermsOk(true)} />
        ) : authed ? (
          <PortalHome clientName={clientName} />
        ) : (
          <PortalLogin
            onLogin={(name, accepted) => {
              setClientName(name);
              setFirmName(localStorage.getItem(FIRM_NAME_KEY) || "");
              setFirmLogo(localStorage.getItem(FIRM_LOGO_KEY) || "");
              setTermsOk(accepted);
              setAuthed(true);
            }}
          />
        )}
      </main>
    </div>
  );
}

function PortalLogin({ onLogin }: { onLogin: (name: string, termsAccepted: boolean) => void }) {
  const { t, setLocale } = useI18n();
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
      localStorage.setItem(FIRM_NAME_KEY, data.firm_name || "");
      localStorage.setItem(FIRM_LOGO_KEY, data.firm_logo || "");
      localStorage.setItem(TERMS_KEY, data.terms_accepted ? "ok" : "pending");
      // Switch the portal UI to the client's preferred communication language
      if (data.locale) setLocale(data.locale);
      onLogin(data.client_name, !!data.terms_accepted);
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

function PortalAcceptTerms({ onAccepted }: { onAccepted: () => void }) {
  const { t } = useI18n();
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function accept() {
    setBusy(true);
    setError("");
    try {
      await portalApi("/accept-terms", { method: "POST", body: JSON.stringify({}) });
      localStorage.setItem(TERMS_KEY, "ok");
      onAccepted();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-md mx-auto mt-12">
      <Card className="p-6 space-y-4">
        <div>
          <h2 className="font-bold text-lg">{t.portalAcceptTermsTitle}</h2>
          <p className="text-sm text-slate-500 mt-1">{t.portalAcceptTermsBody}</p>
        </div>
        <div className="flex gap-4 text-sm">
          <a href="/kushtet" target="_blank" className="text-indigo-600 hover:underline">
            {t.termsOfService}
          </a>
          <a href="/privatesia" target="_blank" className="text-indigo-600 hover:underline">
            {t.privacyPolicy}
          </a>
        </div>
        <label className="flex items-start gap-2 text-sm text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="mt-0.5 accent-indigo-600"
          />
          <span>{t.acceptTosLabel}</span>
        </label>
        <ErrorNote message={error} />
        <Button onClick={accept} disabled={!checked || busy} className="w-full">
          {busy ? t.loading : t.acceptAndContinue}
        </Button>
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
        <PortalDocuments matterId={openMatter.id} />
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
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
        <div className="min-w-0">
          <p className="font-medium text-sm break-words">{sig.document_name}</p>
          {sig.note && <p className="text-xs text-slate-500 mt-0.5">{sig.note}</p>}
        </div>
        {!open && (
          <Button className="shrink-0 self-start sm:self-auto" onClick={() => setOpen(true)}>
            {t.signDocument}
          </Button>
        )}
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

function PortalDocuments({ matterId }: { matterId: string }) {
  const { t } = useI18n();
  const [docs, setDocs] = useState<PortalDoc[]>([]);

  useEffect(() => {
    portalApi<PortalDoc[]>(`/matters/${matterId}/documents`).then(setDocs).catch(() => {});
  }, [matterId]);

  async function download(doc: PortalDoc) {
    const res = await fetch(`${API}/documents/${doc.id}/download`, {
      headers: { Authorization: `Bearer ${portalToken()}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = doc.filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (docs.length === 0) return null;

  return (
    <Card className="p-4 space-y-1">
      <h3 className="font-semibold text-sm text-slate-600 mb-2">📄 {t.documents}</h3>
      {docs.map((d) => (
        <div key={d.id} className="flex items-center justify-between gap-3 py-1.5 text-sm">
          <div className="min-w-0">
            <p className="truncate">{d.filename}</p>
            <p className="text-xs text-slate-400">
              {new Date(d.created_at).toLocaleDateString()} · {(d.size_bytes / 1024).toFixed(0)} KB
            </p>
          </div>
          <button
            onClick={() => download(d)}
            className="shrink-0 text-xs text-indigo-600 hover:underline"
          >
            {t.download}
          </button>
        </div>
      ))}
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
