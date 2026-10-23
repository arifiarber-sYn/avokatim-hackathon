"use client";

import { useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { citizenPost, getCitizenToken } from "@/lib/citizen";
import { Button, ErrorNote, Spinner, Textarea } from "@/components/ui";

/** Inline slot picker: fetch free 30-min slots and reserve one (citizen auth).
 * Shared by the directory cards and the dedicated lawyer profile page. */
export default function BookingWidget({
  profileId,
  prominent = false,
}: {
  profileId: string;
  prominent?: boolean;
}) {
  const { t, locale } = useI18n();
  const [open, setOpen] = useState(false);
  const [slots, setSlots] = useState<string[] | null>(null);
  const [picked, setPicked] = useState("");
  const [note, setNote] = useState("");
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

  async function book(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await citizenPost<{ checkout_url?: string | null }>("/citizen/bookings", {
        profile_id: profileId,
        starts_at: picked,
        note: note.trim() || null,
      });
      if (res.checkout_url) {
        // Paid consultation: finish the booking on Stripe Checkout
        window.location.href = res.checkout_url;
        return;
      }
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
    return prominent ? (
      <Button variant="secondary" onClick={openPicker}>
        📅 {t.bkBook}
      </Button>
    ) : (
      <button
        onClick={openPicker}
        className="text-sm font-medium text-emerald-700 hover:underline"
      >
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

  // Group upcoming slots by day for a compact picker
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
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300"
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
