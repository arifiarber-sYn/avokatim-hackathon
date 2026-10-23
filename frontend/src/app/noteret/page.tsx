"use client";

// Public notary helper (no account needed): which notarial act you need,
// what documents to bring, an indicative fee per AI 02/2012, and the
// directory of all licensed notaries from the public ONK registry.
// Notarization itself always happens in person — the law requires it.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { citizenPost, getCitizenToken } from "@/lib/citizen";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import { Button, Card, ErrorNote, Input, Label, Select, Spinner, Textarea } from "@/components/ui";

interface Notary {
  name: string;
  phone: string;
  email: string;
  address: string;
  city: string;
  // Present only for notary offices registered on the platform
  registered?: boolean;
  profile_id?: string;
  booking?: boolean;
  bio?: string | null;
}

interface NotaryAct {
  code: string;
  act_type: string;
  value_based: boolean;
  per_unit: string | null;
  mandatory_solemnization: boolean;
  name: Record<string, string>;
  checklist: { key: string; label: Record<string, string> }[];
}

function StampIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M12 3a3 3 0 0 0-3 3c0 1.4.8 2.5 1.5 3.4.5.7.5 1.6-.3 1.6H8a2 2 0 0 0-2 2v1h12v-1a2 2 0 0 0-2-2h-2.2c-.8 0-.8-.9-.3-1.6.7-.9 1.5-2 1.5-3.4a3 3 0 0 0-3-3z" strokeLinejoin="round" />
      <path d="M5 18h14v3H5z" strokeLinejoin="round" />
    </svg>
  );
}

export default function NotariesPage() {
  const { t, locale } = useI18n();
  const [notaries, setNotaries] = useState<Notary[] | null>(null);
  const [cities, setCities] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [city, setCity] = useState("");

  const [acts, setActs] = useState<NotaryAct[]>([]);
  const [actCode, setActCode] = useState("");
  const [value, setValue] = useState("");
  const [units, setUnits] = useState("1");
  const [fee, setFee] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/public/tools/notaries")
      .then((r) => r.json())
      .then((d) => {
        setNotaries(d.notaries);
        setCities(d.cities);
        setTotal(d.total);
      })
      .catch(() => setNotaries([]));
    fetch("/api/public/tools/notary-acts")
      .then((r) => r.json())
      .then((d) => setActs(d.acts))
      .catch(() => setActs([]));
  }, []);

  const loc = (m: Record<string, string>) => m[locale] || m.sq || "";
  const act = acts.find((a) => a.code === actCode);
  const shown = useMemo(
    () => (notaries || []).filter((n) => !city || n.city === city),
    [notaries, city]
  );

  const typeLabel = (type: string) =>
    type === "akt" ? t.ntTypeAkt : type === "solemnizim" ? t.ntTypeSolemnizim : t.ntTypeVertetim;

  async function estimate(e: React.FormEvent) {
    e.preventDefault();
    if (!act) return;
    setBusy(true);
    setError("");
    setFee(null);
    try {
      const res = await fetch("/api/public/tools/notary-fee", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          act_code: act.code,
          value_eur: act.value_based ? Number(value) : undefined,
          units: act.per_unit ? Number(units) || 1 : 1,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || t.error);
      setFee((await res.json()).fee_eur);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell wide>
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-6 space-y-5">
        <div className="flex items-center gap-2.5">
          <StampIcon className="h-6 w-6 text-indigo-600" />
          <h1 className="text-2xl font-bold">{t.ntTitle}</h1>
          {total > 0 && (
            <span className="text-sm text-slate-400 mt-1">
              {total} {t.ntCount}
            </span>
          )}
        </div>

        <PageIntro k="noteret" title={t.ntIntroT} body={t.ntIntro} />

        <div className="grid md:grid-cols-2 gap-5 items-start">
          {/* Fee estimator + checklist */}
          <Card className="p-5 space-y-4">
            <h2 className="font-semibold text-slate-900">{t.ntFeeTitle}</h2>
            <form onSubmit={estimate} className="space-y-3">
              <div>
                <Label>{t.ntActLabel}</Label>
                <Select
                  value={actCode}
                  onChange={(e) => {
                    setActCode(e.target.value);
                    setFee(null);
                  }}
                  required
                >
                  <option value="">—</option>
                  {acts.map((a) => (
                    <option key={a.code} value={a.code}>
                      {loc(a.name)}
                    </option>
                  ))}
                </Select>
                {act && (
                  <p className="text-xs text-indigo-600 mt-1.5 font-medium">{typeLabel(act.act_type)}</p>
                )}
              </div>

              {act?.value_based && (
                <div>
                  <Label>{t.ntValueLabel}</Label>
                  <Input
                    type="number"
                    min="1"
                    step="any"
                    value={value}
                    onChange={(e) => { setValue(e.target.value); setFee(null); }}
                    required
                  />
                </div>
              )}
              {act?.per_unit && (
                <div>
                  <Label>{t.ntUnitsLabel}</Label>
                  <Input
                    type="number"
                    min="1"
                    max="500"
                    value={units}
                    onChange={(e) => { setUnits(e.target.value); setFee(null); }}
                    required
                  />
                </div>
              )}

              {act?.mandatory_solemnization && (
                <p className="text-xs bg-indigo-50 text-indigo-800 rounded-lg p-2.5">{t.ntMandatoryNote}</p>
              )}

              <ErrorNote message={error} />
              <Button type="submit" disabled={busy || !act} className="w-full">
                {busy ? t.loading : t.ntCalc}
              </Button>
            </form>

            {fee !== null && (
              <div className="rounded-xl bg-indigo-50 border border-indigo-200 p-4 space-y-1">
                <p className="text-sm text-indigo-700 font-semibold">{t.ntFeeResult}</p>
                <p className="text-3xl font-extrabold text-indigo-900">~{fee} €</p>
                <p className="text-xs text-indigo-700">{t.ntFeeBasis}</p>
              </div>
            )}

            {act && act.checklist.length > 0 && (
              <div className="border-t border-slate-100 pt-3">
                <p className="text-sm font-semibold text-slate-700 mb-2">✓ {t.ntChecklistTitle}</p>
                <ul className="space-y-1.5">
                  {act.checklist.map((item) => (
                    <li key={item.key} className="text-sm text-slate-600 flex gap-2">
                      <span className="text-indigo-500 shrink-0">•</span>
                      {loc(item.label)}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Link
              href="/dokumentet"
              className="block text-center text-sm font-medium text-indigo-600 hover:underline"
            >
              {t.ntDocsHint} →
            </Link>
          </Card>

          {/* Directory */}
          <div className="space-y-3">
            <div>
              <Label>{t.ntPickCity}</Label>
              <Select value={city} onChange={(e) => setCity(e.target.value)}>
                <option value="">{t.ntAllCities}</option>
                {cities.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
            </div>

            {notaries === null ? (
              <Spinner />
            ) : (
              <div className="space-y-2 max-h-[32rem] overflow-y-auto pr-1">
                {shown.map((n) => (
                  <div
                    key={`${n.name}-${n.city}`}
                    className={`bg-white rounded-xl border p-4 ${
                      n.registered ? "border-violet-200 ring-1 ring-violet-100" : "border-slate-200"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                        {n.name}
                        {n.registered && (
                          <span className="text-[10px] font-semibold bg-violet-100 text-violet-700 rounded-full px-2 py-0.5">
                            ✓ {t.ntRegistered}
                          </span>
                        )}
                      </p>
                      <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5 shrink-0">
                        {n.city}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 mt-0.5">{n.address}</p>
                    {n.bio && <p className="text-xs text-slate-500 mt-1">{n.bio}</p>}
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm">
                      {n.phone && (
                        <a href={`tel:${n.phone.replace(/[^+\d]/g, "")}`} className="text-indigo-600 hover:underline">
                          ☎ {n.phone}
                        </a>
                      )}
                      {n.email && (
                        <a href={`mailto:${n.email}`} className="text-indigo-600 hover:underline break-all">
                          ✉ {n.email}
                        </a>
                      )}
                    </div>
                    {n.booking && n.profile_id && (
                      <div className="mt-2">
                        <NotaryBookingWidget profileId={n.profile_id} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            <p className="text-[11px] text-slate-400">{t.ntSource}</p>
          </div>
        </div>

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.ntPresenceNote}</p>

        {/* Supply-side recruitment: the notary's own digital office */}
        <Link
          href="/per-noteret"
          className="block rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white p-5 text-center shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all"
        >
          <span className="text-sm font-semibold">{t.npLinkFromNoteret} →</span>
        </Link>
      </main>
    </PublicShell>
  );
}

/** Slot picker for registered notary offices. Same flow as the lawyer
 * directory, plus an optional "prepared dossier": the citizen attaches the
 * draft PDF generated at /dokumentet so the notary sees it before the visit. */
function NotaryBookingWidget({ profileId }: { profileId: string }) {
  const { t, locale } = useI18n();
  const [open, setOpen] = useState(false);
  const [slots, setSlots] = useState<string[] | null>(null);
  const [picked, setPicked] = useState("");
  const [note, setNote] = useState("");
  const [attachment, setAttachment] = useState<{ name: string; b64: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function openPicker() {
    setOpen(true);
    if (slots !== null) return;
    try {
      const res = await fetch(`/api/public/lawyers/${profileId}/slots`);
      const data = await res.json();
      setSlots(data.slots || []);
    } catch {
      setSlots([]);
    }
  }

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      setError(t.bkAttachTooBig);
      return;
    }
    setError("");
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setAttachment({ name: file.name, b64: dataUrl.split(",")[1] || "" });
    };
    reader.readAsDataURL(file);
  }

  async function book(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await citizenPost("/citizen/bookings", {
        profile_id: profileId,
        starts_at: picked,
        note: note.trim() || null,
        attachment_name: attachment?.name || null,
        attachment_b64: attachment?.b64 || null,
      });
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.error);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <p className="text-xs bg-emerald-50 text-emerald-700 rounded-lg px-3 py-2">{t.bkBooked}</p>
    );
  }

  if (!open) {
    return (
      <button onClick={openPicker} className="text-sm font-medium text-violet-700 hover:underline">
        📅 {t.bkBook}
      </button>
    );
  }

  if (!getCitizenToken()) {
    return (
      <p className="text-xs bg-amber-50 text-amber-800 rounded-lg px-3 py-2">
        {t.bkLoginFirst}{" "}
        <Link href="/rasti-im" className="underline font-medium">
          {t.mkMyCase} →
        </Link>
      </p>
    );
  }

  const byDay = new Map<string, string[]>();
  for (const s of slots || []) {
    const day = new Date(s).toLocaleDateString(locale, {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
    byDay.set(day, [...(byDay.get(day) || []), s]);
  }

  return (
    <div className="border-t border-slate-100 pt-3 space-y-2">
      <p className="text-xs font-semibold text-slate-600">{t.bkPickSlot}</p>
      {slots === null ? (
        <Spinner />
      ) : slots.length === 0 ? (
        <p className="text-xs text-slate-500">{t.bkNoSlots}</p>
      ) : (
        <form onSubmit={book} className="space-y-2">
          <div className="space-y-1.5 max-h-44 overflow-y-auto">
            {[...byDay.entries()].map(([day, daySlots]) => (
              <div key={day} className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] text-slate-400 w-24 shrink-0">{day}</span>
                {daySlots.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setPicked(s)}
                    className={`text-xs rounded-md px-2 py-1 border transition ${
                      picked === s
                        ? "bg-violet-600 border-violet-600 text-white"
                        : "bg-white border-slate-200 text-slate-600 hover:border-violet-300"
                    }`}
                  >
                    {new Date(s).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}
                  </button>
                ))}
              </div>
            ))}
          </div>
          {picked && (
            <>
              <Textarea
                rows={2}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder={t.bkNote}
              />
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  {t.bkAttachLabel}
                </label>
                <input type="file" accept=".pdf,application/pdf" onChange={onFile} className="text-xs" />
                {attachment && (
                  <p className="text-[11px] text-emerald-700 mt-0.5">✓ {attachment.name}</p>
                )}
                <p className="text-[11px] text-slate-400 mt-0.5">{t.bkAttachHint}</p>
              </div>
              <ErrorNote message={error} />
              <Button type="submit" disabled={busy} className="w-full">
                {busy ? t.loading : t.bkConfirmBook}
              </Button>
            </>
          )}
        </form>
      )}
    </div>
  );
}
