"use client";

/** Consultation/appointment reservations from the public directories
 * (/avokatet for lawyers, /noteret for notaries). Shared between the
 * marketplace page (lawyers) and the dashboard (notary offices, which
 * have no marketplace). */
import { useCallback, useEffect, useState } from "react";
import { apiDownload, apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Card } from "@/components/ui";

interface LawyerBooking {
  id: string;
  starts_at: string;
  status: string;
  note: string | null;
  with: string | null;
  citizen_email: string;
  attachment_name: string | null;
}

export default function BookingsPanel() {
  const { t, locale } = useI18n();
  const [bookings, setBookings] = useState<LawyerBooking[] | null>(null);

  const load = useCallback(() => {
    apiGet<LawyerBooking[]>("/marketplace/bookings").then(setBookings).catch(() => setBookings([]));
  }, []);

  useEffect(load, [load]);

  if (!bookings || bookings.length === 0) return null;

  const statusLabel: Record<string, string> = {
    pending: t.bkStatusPending,
    confirmed: t.bkStatusConfirmed,
    declined: t.bkStatusDeclined,
    cancelled: t.bkStatusCancelled,
  };
  const statusTone: Record<string, string> = {
    pending: "bg-amber-50 text-amber-700",
    confirmed: "bg-emerald-50 text-emerald-700",
    declined: "bg-red-50 text-red-700",
    cancelled: "bg-slate-100 text-slate-500",
  };

  async function decide(id: string, action: "confirm" | "decline") {
    try {
      await apiPost(`/marketplace/bookings/${id}/decide`, { action });
      load();
    } catch {}
  }

  return (
    <Card className="p-5 space-y-3">
      <h2 className="font-semibold">📅 {t.bkLawyerPanelT}</h2>
      <div className="space-y-2">
        {bookings.map((b) => (
          <div key={b.id} className="flex items-start justify-between gap-3 flex-wrap text-sm border-b border-slate-50 pb-2 last:border-0 last:pb-0">
            <div className="space-y-0.5 min-w-0">
              <p className="font-medium text-slate-700">
                {new Date(b.starts_at).toLocaleString(locale, {
                  weekday: "short", day: "numeric", month: "short",
                  hour: "2-digit", minute: "2-digit",
                })}
                <span className={`ml-2 text-xs rounded-full px-2 py-0.5 ${statusTone[b.status] || ""}`}>
                  {statusLabel[b.status] || b.status}
                </span>
              </p>
              <p className="text-xs text-slate-500">
                {b.with} · {b.citizen_email}
              </p>
              {b.note && <p className="text-xs text-slate-600 bg-slate-50 rounded px-2 py-1">{b.note}</p>}
              {b.attachment_name && (
                <button
                  onClick={() =>
                    apiDownload(`/marketplace/bookings/${b.id}/attachment`, b.attachment_name || "dosja.pdf")
                  }
                  className="text-xs font-medium text-violet-700 hover:underline"
                >
                  📎 {t.bkDossierDl}: {b.attachment_name}
                </button>
              )}
            </div>
            {b.status === "pending" && (
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => decide(b.id, "confirm")}
                  className="text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg px-3 py-1.5"
                >
                  {t.bkConfirm}
                </button>
                <button
                  onClick={() => decide(b.id, "decline")}
                  className="text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg px-3 py-1.5"
                >
                  {t.bkDecline}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
