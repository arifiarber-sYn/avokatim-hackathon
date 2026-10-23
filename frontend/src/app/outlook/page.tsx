"use client";

/**
 * Outlook add-in taskpane (D-059 F8): "Save this email to a matter".
 * Runs inside Outlook (desktop/web) as an iframe — Office.js comes from the
 * Microsoft CDN (targeted CSP exception in proxy.ts, this route only).
 * Flow: lawyer login (JWT in localStorage, same as the app) -> search
 * matter -> save: body becomes a note, attachments run through the normal
 * document pipeline via POST /api/matters/{id}/import-email.
 */
import { useEffect, useState } from "react";
import Script from "next/script";
import { apiGet, apiPost, getToken, setToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Matter } from "@/lib/types";
import { Button, ErrorNote, Input, Label, Spinner } from "@/components/ui";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare const Office: any;

interface OutlookEmail {
  subject: string;
  sender: string;
  receivedAt: string;
  body: string;
  attachments: { name: string; content_base64: string }[];
}

function readCurrentEmail(): Promise<OutlookEmail> {
  return new Promise((resolve, reject) => {
    const item = Office?.context?.mailbox?.item;
    if (!item) {
      reject(new Error("No email selected"));
      return;
    }
    item.body.getAsync(Office.CoercionType.Text, async (result: any) => {
      if (result.status !== Office.AsyncResultStatus.Succeeded) {
        reject(new Error("Could not read the email body"));
        return;
      }
      const attachments: OutlookEmail["attachments"] = [];
      for (const att of item.attachments || []) {
        if (att.isInline) continue;
        const content = await new Promise<string | null>((res) => {
          item.getAttachmentContentAsync(att.id, (r: any) => {
            res(
              r.status === Office.AsyncResultStatus.Succeeded &&
                r.value.format === Office.MailboxEnums.AttachmentContentFormat.Base64
                ? (r.value.content as string)
                : null
            );
          });
        });
        if (content) attachments.push({ name: att.name, content_base64: content });
      }
      resolve({
        subject: item.subject || "",
        sender: item.from?.emailAddress || "",
        receivedAt: item.dateTimeCreated
          ? new Date(item.dateTimeCreated).toLocaleString()
          : "",
        body: (result.value as string) || "",
        attachments,
      });
    });
  });
}

export default function OutlookTaskpane() {
  const { t } = useI18n();
  const [officeReady, setOfficeReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [matters, setMatters] = useState<Matter[]>([]);
  const [query, setQuery] = useState("");
  const [matterId, setMatterId] = useState("");

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, []);

  useEffect(() => {
    if (!authed) return;
    apiGet<Matter[]>("/matters").then(setMatters).catch(() => setAuthed(false));
  }, [authed]);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await apiPost<{ access_token: string; requires_2fa: boolean }>(
        "/auth/login",
        { email, password }
      );
      if (r.requires_2fa) {
        // Keep the taskpane simple: 2FA accounts log in via the app first —
        // the token in localStorage is shared with the taskpane.
        setError(t.olk2fa);
        return;
      }
      setToken(r.access_token);
      setAuthed(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (!matterId) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const mail = await readCurrentEmail();
      const result = await apiPost<{ documents: number; skipped: string[] }>(
        `/matters/${matterId}/import-email`,
        {
          subject: mail.subject,
          sender: mail.sender,
          received_at: mail.receivedAt,
          body: mail.body,
          attachments: mail.attachments,
        }
      );
      setNotice(
        t.olkSaved.replace("{n}", String(result.documents)) +
          (result.skipped.length ? ` (${t.olkSkipped}: ${result.skipped.join(", ")})` : "")
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  const filtered = query.trim()
    ? matters.filter(
        (m) =>
          m.title.toLowerCase().includes(query.toLowerCase()) ||
          m.reference.toLowerCase().includes(query.toLowerCase())
      )
    : matters;

  return (
    <div className="min-h-screen bg-slate-50 p-4 text-sm">
      <Script
        src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js"
        strategy="afterInteractive"
        onReady={() => {
          Office.onReady(() => setOfficeReady(true));
        }}
      />
      <h1 className="text-base font-bold text-slate-800 mb-1">✦ {t.olkTitle}</h1>
      <p className="text-xs text-slate-500 mb-4">{t.olkSubtitle}</p>
      <ErrorNote message={error} />
      {notice && (
        <p className="text-xs bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg px-3 py-2 mb-3">
          ✓ {notice}
        </p>
      )}

      {!authed ? (
        <form onSubmit={login} className="space-y-3 max-w-sm">
          <div>
            <Label>Email</Label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <Label>{t.password}</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" disabled={busy}>
            {busy ? t.loading : t.login}
          </Button>
        </form>
      ) : (
        <div className="space-y-3">
          <div>
            <Label>{t.olkPickMatter}</Label>
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t.search}
            />
          </div>
          <div className="max-h-64 overflow-auto space-y-1 border border-slate-200 rounded-lg bg-white p-1">
            {matters.length === 0 && <Spinner />}
            {filtered.slice(0, 30).map((m) => (
              <button
                key={m.id}
                onClick={() => setMatterId(m.id)}
                className={`w-full text-left rounded-md px-2.5 py-1.5 text-xs transition ${
                  matterId === m.id
                    ? "bg-indigo-600 text-white"
                    : "hover:bg-slate-100 text-slate-700"
                }`}
              >
                <span className="font-medium">{m.reference}</span> — {m.title}
              </button>
            ))}
          </div>
          <Button onClick={save} disabled={busy || !matterId || !officeReady}>
            {busy ? t.loading : t.olkSaveBtn}
          </Button>
          {!officeReady && (
            <p className="text-xs text-slate-400">{t.olkOutsideOutlook}</p>
          )}
        </div>
      )}
    </div>
  );
}
