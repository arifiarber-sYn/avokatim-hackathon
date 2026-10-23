"use client";

// Citizen's evidence vault: encrypted recordings with hash-chain custody.
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { citizenDownload, citizenGet } from "@/lib/citizen";
import { Card } from "@/components/ui";

export interface EvidenceSessionInfo {
  id: string;
  case_request_id: string | null;
  kind: string;
  mime: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  chunk_count: number;
  total_bytes: number;
  chain_hash: string | null;
  transcript: string | null;
  transcript_status: string;
}

export default function EvidenceVault({ refreshKey }: { refreshKey: number }) {
  const { t, locale } = useI18n();
  const [sessions, setSessions] = useState<EvidenceSessionInfo[] | null>(null);

  useEffect(() => {
    citizenGet<EvidenceSessionInfo[]>("/citizen/evidence")
      .then(setSessions)
      .catch(() => setSessions([]));
  }, [refreshKey]);

  if (sessions === null || sessions.length === 0) return null;

  return (
    <Card className="p-5 space-y-3">
      <div>
        <h2 className="font-semibold">🔒 {t.evVaultT}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{t.evVaultHint}</p>
      </div>
      <div className="space-y-2">
        {sessions.map((s) => (
          <div key={s.id} className="border border-slate-200 rounded-lg px-3 py-2 space-y-1.5">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <span className="font-medium">
                {new Date(s.started_at).toLocaleString(locale)}
              </span>
              <span className="text-xs text-slate-500">
                {s.chunk_count} {t.evChunksWord} · {(s.total_bytes / 1024).toFixed(0)} KB
              </span>
              {s.status === "recording" && (
                <span className="text-xs text-red-600 font-semibold">●</span>
              )}
              <span className="flex gap-3 ml-auto text-sm">
                <button
                  onClick={() =>
                    citizenDownload(`/citizen/evidence/${s.id}/audio`, `deshmia-${s.id}.webm`)
                  }
                  className="text-indigo-600 font-medium hover:underline"
                >
                  ⬇ {t.evAudioBtn}
                </button>
                <button
                  onClick={() =>
                    citizenDownload(`/citizen/evidence/${s.id}/package`, `pako-deshmie-${s.id}.pdf`)
                  }
                  className="text-indigo-600 font-medium hover:underline"
                >
                  ⬇ {t.evPdfBtn}
                </button>
              </span>
            </div>
            {s.transcript ? (
              <p className="text-xs text-slate-600 bg-slate-50 rounded p-2 line-clamp-3">
                {s.transcript}
              </p>
            ) : s.transcript_status === "pending" ? (
              <p className="text-xs text-slate-400">{t.evTranscriptPending}</p>
            ) : null}
          </div>
        ))}
      </div>
    </Card>
  );
}
