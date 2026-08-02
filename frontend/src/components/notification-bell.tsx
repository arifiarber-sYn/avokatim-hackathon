"use client";

/** In-app notification center (D-054): bell with unread badge, live count
 * via SSE (poll fallback), dropdown on desktop / bottom sheet on mobile. */
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost, getToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

interface NotificationItem {
  id: string;
  kind: string;
  title: string;
  body: string | null;
  url: string | null;
  read_at: string | null;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

function timeAgo(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 60) return `${mins}m`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h`;
  return new Date(iso).toLocaleDateString();
}

export function NotificationBell({ dark = false }: { dark?: boolean }) {
  const { t } = useI18n();
  const router = useRouter();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[] | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);
  const stopRef = useRef(false);

  const refreshCount = useCallback(() => {
    apiGet<{ unread: number }>("/notifications/unread-count")
      .then((r) => setUnread(r.unread))
      .catch(() => {});
  }, []);

  // Live unread count: SSE stream with automatic reconnect; window focus
  // refresh doubles as the fallback when the stream is unavailable.
  useEffect(() => {
    stopRef.current = false;
    refreshCount();

    async function stream() {
      while (!stopRef.current) {
        try {
          const res = await fetch(`${API_BASE}/notifications/stream`, {
            headers: { Authorization: `Bearer ${getToken() || ""}` },
          });
          if (!res.ok || !res.body) throw new Error("stream unavailable");
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buf = "";
          for (;;) {
            const { done, value } = await reader.read();
            if (done || stopRef.current) break;
            buf += decoder.decode(value, { stream: true });
            const parts = buf.split("\n\n");
            buf = parts.pop() || "";
            for (const part of parts) {
              const line = part.split("\n").find((l) => l.startsWith("data: "));
              if (!line) continue;
              try {
                const data = JSON.parse(line.slice(6));
                if (typeof data.unread === "number") setUnread(data.unread);
              } catch {
                /* keepalive */
              }
            }
          }
        } catch {
          /* fall through to retry */
        }
        if (!stopRef.current) await new Promise((r) => setTimeout(r, 60_000));
      }
    }
    stream();

    const onFocus = () => refreshCount();
    window.addEventListener("focus", onFocus);
    return () => {
      stopRef.current = true;
      window.removeEventListener("focus", onFocus);
    };
  }, [refreshCount]);

  // Click outside closes the desktop dropdown
  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next) {
      try {
        setItems(await apiGet<NotificationItem[]>("/notifications?limit=30"));
      } catch {
        setItems([]);
      }
    }
  }

  async function openItem(n: NotificationItem) {
    setOpen(false);
    if (!n.read_at) {
      setUnread((u) => Math.max(0, u - 1));
      apiPost(`/notifications/${n.id}/read`).catch(() => {});
    }
    if (n.url) router.push(n.url);
  }

  async function markAll() {
    setUnread(0);
    setItems((list) =>
      list ? list.map((n) => ({ ...n, read_at: n.read_at || new Date().toISOString() })) : list
    );
    apiPost("/notifications/read-all").catch(() => {});
  }

  const list = (
    <div className="flex flex-col max-h-[70vh] md:max-h-[28rem]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <p className="text-sm font-semibold text-slate-800">{t.ntfTitle}</p>
        {unread > 0 && (
          <button onClick={markAll} className="text-xs text-indigo-600 hover:underline py-1">
            {t.ntfMarkAll}
          </button>
        )}
      </div>
      <div className="overflow-y-auto overscroll-contain divide-y divide-slate-50">
        {items === null && <p className="px-4 py-6 text-sm text-slate-400">{t.loading}</p>}
        {items?.length === 0 && (
          <p className="px-4 py-8 text-sm text-slate-400 text-center">{t.ntfEmpty}</p>
        )}
        {items?.map((n) => (
          <button
            key={n.id}
            onClick={() => openItem(n)}
            className={`w-full text-left px-4 py-3 hover:bg-slate-50 transition ${
              n.read_at ? "opacity-60" : ""
            }`}
          >
            <span className="flex items-start gap-2.5">
              {!n.read_at && (
                <span className="mt-1.5 h-2 w-2 rounded-full bg-indigo-500 shrink-0" />
              )}
              <span className="min-w-0 flex-1">
                <span className="block text-sm text-slate-800 leading-snug">{n.title}</span>
                {n.body && (
                  <span className="block text-xs text-slate-500 truncate mt-0.5">{n.body}</span>
                )}
              </span>
              <span className="text-[10px] text-slate-400 shrink-0 mt-0.5">
                {timeAgo(n.created_at)}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div ref={boxRef} className="relative">
      <button
        onClick={toggle}
        aria-label={t.ntfTitle}
        className={`relative p-2 rounded-lg transition ${
          dark ? "text-slate-200 hover:bg-slate-800" : "text-slate-600 hover:bg-slate-100"
        }`}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        {unread > 0 && (
          <span className="absolute top-0.5 right-0.5 min-w-[16px] h-4 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center px-1">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {/* Desktop dropdown */}
      {open && (
        <div className="hidden md:block absolute right-0 mt-1 w-96 rounded-xl border border-slate-200 bg-white shadow-xl z-50">
          {list}
        </div>
      )}

      {/* Mobile bottom sheet */}
      {open && (
        <div className="md:hidden fixed inset-0 z-[60]">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <div className="absolute inset-x-0 bottom-0 bg-white rounded-t-2xl shadow-2xl pb-[env(safe-area-inset-bottom)]">
            <div className="mx-auto mt-2 h-1 w-10 rounded-full bg-slate-200" />
            {list}
          </div>
        </div>
      )}
    </div>
  );
}
