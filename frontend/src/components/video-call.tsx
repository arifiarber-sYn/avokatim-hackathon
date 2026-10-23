"use client";

/**
 * SOS video/audio call overlay (LiveKit). Used by both sides of a claimed
 * marketplace case: the lawyer (Tregu) and the citizen (/rasti-im).
 * The server decides whether video is enabled; when it is not, we show a
 * friendly note instead of a broken call.
 *
 * Call recording (D-018): instead of a server-side Egress container, the
 * citizen can record the call locally — both audio sides are mixed with the
 * Web Audio API and streamed in 5 s chunks to the encrypted evidence vault.
 * The lawyer is shown a consent notice before joining.
 */
import { useEffect, useRef, useState } from "react";
import {
  ConnectionState,
  RemoteTrack,
  Room,
  RoomEvent,
  Track,
} from "livekit-client";
import { useI18n } from "@/lib/i18n";
import { citizenPost, citizenUpload } from "@/lib/citizen";
import { pickRecorderMime } from "@/lib/voice";

export interface CallGrant {
  enabled: boolean;
  room: string;
  token: string | null;
  identity: string;
  url: string | null;
}

/** Signaling URL: explicit from the server, or derived from where the app
 * itself is served (ws:// locally, wss:// through Caddy :7443 on the LAN). */
function signalUrl(grant: CallGrant): string {
  if (grant.url) return grant.url;
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return "ws://127.0.0.1:7880";
  return `wss://${host}:7443`;
}

export default function VideoCall({
  fetchGrant,
  onClose,
  recordCaseId,
  showRecordNotice,
}: {
  fetchGrant: () => Promise<CallGrant>;
  onClose: () => void;
  /** Citizen side: id of the case — enables "record as evidence". */
  recordCaseId?: string;
  /** Lawyer side: require acknowledging that the call may be recorded. */
  showRecordNotice?: boolean;
}) {
  const { t } = useI18n();
  const [accepted, setAccepted] = useState(!showRecordNotice);
  const [phase, setPhase] = useState<"connecting" | "waiting" | "live" | "off" | "error">(
    "connecting"
  );
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [recState, setRecState] = useState<"off" | "starting" | "on">("off");
  const roomRef = useRef<Room | null>(null);
  const localRef = useRef<HTMLDivElement>(null);
  const remoteRef = useRef<HTMLDivElement>(null);

  // --- call recording (citizen only)
  const audioCtxRef = useRef<AudioContext | null>(null);
  const mixDestRef = useRef<MediaStreamAudioDestinationNode | null>(null);
  const recRef = useRef<MediaRecorder | null>(null);
  const recSessionRef = useRef<string | null>(null);
  const seqRef = useRef(0);
  const uploadChainRef = useRef<Promise<void>>(Promise.resolve());
  const mixedTracksRef = useRef<Set<MediaStreamTrack>>(new Set());

  /** Feed an audio track into the mix (local mic or remote participant). */
  function mixTrack(track: MediaStreamTrack) {
    const ctx = audioCtxRef.current;
    const dest = mixDestRef.current;
    if (!ctx || !dest || mixedTracksRef.current.has(track)) return;
    mixedTracksRef.current.add(track);
    ctx.createMediaStreamSource(new MediaStream([track])).connect(dest);
  }

  useEffect(() => {
    if (!accepted) return;
    let cancelled = false;
    const room = new Room({ adaptiveStream: true, dynacast: true });
    roomRef.current = room;

    function attachRemote(track: RemoteTrack) {
      if (track.kind !== Track.Kind.Video && track.kind !== Track.Kind.Audio) return;
      const el = track.attach();
      if (track.kind === Track.Kind.Video && remoteRef.current) {
        el.className = "w-full h-full object-cover rounded-xl";
        remoteRef.current.replaceChildren(el);
      } else {
        el.style.display = "none";
        document.body.appendChild(el);
      }
      if (track.kind === Track.Kind.Audio && track.mediaStreamTrack) {
        mixTrack(track.mediaStreamTrack);
      }
      setPhase("live");
    }

    async function start() {
      let grant: CallGrant;
      try {
        grant = await fetchGrant();
      } catch {
        if (!cancelled) setPhase("error");
        return;
      }
      if (!grant.enabled || !grant.token) {
        if (!cancelled) setPhase("off");
        return;
      }
      room
        .on(RoomEvent.TrackSubscribed, attachRemote)
        .on(RoomEvent.TrackUnsubscribed, (track) => track.detach().forEach((el) => el.remove()))
        .on(RoomEvent.ParticipantDisconnected, () => {
          remoteRef.current?.replaceChildren();
          setPhase("waiting");
        })
        .on(RoomEvent.ConnectionStateChanged, (state) => {
          if (state === ConnectionState.Disconnected && !cancelled) setPhase("error");
        });
      try {
        await room.connect(signalUrl(grant), grant.token);
        await room.localParticipant.enableCameraAndMicrophone();
        const camPub = room.localParticipant.getTrackPublication(Track.Source.Camera);
        if (camPub?.track && localRef.current) {
          const el = camPub.track.attach();
          el.className = "w-full h-full object-cover rounded-lg scale-x-[-1]";
          localRef.current.replaceChildren(el);
        }
        // A participant may already be in the room before we subscribe
        for (const participant of room.remoteParticipants.values()) {
          for (const pub of participant.trackPublications.values()) {
            if (pub.track) attachRemote(pub.track as RemoteTrack);
          }
        }
        if (!cancelled) {
          setPhase((p) => (p === "live" ? p : "waiting"));
        }
      } catch {
        if (!cancelled) setPhase("error");
      }
    }

    start();
    return () => {
      cancelled = true;
      void stopRecording();
      room.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accepted]);

  // ---------- recording ----------

  function queueChunk(blob: Blob) {
    const sessionId = recSessionRef.current;
    if (!sessionId) return;
    const seq = seqRef.current++;
    // Chunks must arrive in order (hash chain) — serialize uploads
    uploadChainRef.current = uploadChainRef.current.then(async () => {
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const form = new FormData();
          form.append("seq", String(seq));
          form.append("chunk", blob, `chunk-${seq}.webm`);
          await citizenUpload(`/citizen/evidence/${sessionId}/chunks`, form);
          return;
        } catch {
          await new Promise((r) => setTimeout(r, 1500 * (attempt + 1)));
        }
      }
    });
  }

  async function startRecording() {
    if (!recordCaseId || recState !== "off") return;
    setRecState("starting");
    try {
      const mime = pickRecorderMime();
      const session = await citizenPost<{ id: string }>("/citizen/evidence/start", {
        kind: "call",
        mime,
        consent: true,
        case_request_id: recordCaseId,
      });
      recSessionRef.current = session.id;
      seqRef.current = 0;

      const ctx = new AudioContext();
      audioCtxRef.current = ctx;
      mixDestRef.current = ctx.createMediaStreamDestination();
      // Local mic
      const micPub = roomRef.current?.localParticipant.getTrackPublication(
        Track.Source.Microphone
      );
      if (micPub?.track?.mediaStreamTrack) mixTrack(micPub.track.mediaStreamTrack);
      // Remote audio already in the room
      for (const participant of roomRef.current?.remoteParticipants.values() || []) {
        for (const pub of participant.trackPublications.values()) {
          if (pub.track?.kind === Track.Kind.Audio && pub.track.mediaStreamTrack) {
            mixTrack(pub.track.mediaStreamTrack);
          }
        }
      }

      const rec = new MediaRecorder(mixDestRef.current.stream, { mimeType: mime });
      recRef.current = rec;
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) queueChunk(e.data);
      };
      rec.start(5000);
      setRecState("on");
    } catch {
      setRecState("off");
      recSessionRef.current = null;
    }
  }

  async function stopRecording() {
    const rec = recRef.current;
    if (rec && rec.state !== "inactive") rec.stop();
    recRef.current = null;
    mixedTracksRef.current.clear();
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    mixDestRef.current = null;
    setRecState("off");
    const sessionId = recSessionRef.current;
    recSessionRef.current = null;
    if (sessionId) {
      // Let the final ondataavailable fire, then flush the queue and finish
      await new Promise((r) => setTimeout(r, 400));
      await uploadChainRef.current;
      try {
        await citizenPost(`/citizen/evidence/${sessionId}/finish`, {
          case_request_id: recordCaseId,
        });
      } catch {}
    }
  }

  async function toggleMic() {
    const room = roomRef.current;
    if (!room) return;
    await room.localParticipant.setMicrophoneEnabled(!micOn);
    setMicOn(!micOn);
  }

  async function toggleCam() {
    const room = roomRef.current;
    if (!room) return;
    await room.localParticipant.setCameraEnabled(!camOn);
    setCamOn(!camOn);
  }

  function hangUp() {
    void stopRecording();
    roomRef.current?.disconnect();
    onClose();
  }

  // Lawyer side: acknowledge the recording notice before joining
  if (!accepted) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950/95 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-6 max-w-md w-full space-y-4">
          <h2 className="font-bold text-slate-900">{t.callRecNoticeT}</h2>
          <p className="text-sm text-slate-600 leading-relaxed">{t.callRecNotice}</p>
          <div className="flex gap-2 justify-end">
            <button
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
            >
              {t.cancel}
            </button>
            <button
              onClick={() => setAccepted(true)}
              className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 text-sm font-medium"
            >
              {t.callRecAccept}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 flex flex-col items-center justify-center p-4">
      {recState === "on" && (
        <p className="mb-3 text-xs font-bold text-red-300 bg-red-950/70 border border-red-800 rounded-full px-4 py-1.5 flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
          </span>
          {t.callRecLive}
        </p>
      )}
      <div className="relative w-full max-w-3xl aspect-video bg-slate-900 rounded-xl overflow-hidden">
        <div ref={remoteRef} className="absolute inset-0 flex items-center justify-center" />
        {phase !== "live" && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-slate-300 text-sm text-center px-6">
              {phase === "connecting" && t.mkCallConnecting}
              {phase === "waiting" && t.mkCallWaiting}
              {phase === "off" && t.mkCallNotConfigured}
              {phase === "error" && t.mkCallFailed}
            </p>
          </div>
        )}
        <div
          ref={localRef}
          className="absolute bottom-3 right-3 w-32 sm:w-44 aspect-video bg-slate-800 rounded-lg overflow-hidden shadow-lg"
        />
      </div>
      <div className="flex items-center gap-3 mt-4 flex-wrap justify-center">
        {phase !== "off" && phase !== "error" && (
          <>
            <button
              onClick={toggleMic}
              className={`rounded-full px-4 py-2 text-sm font-medium ${
                micOn ? "bg-slate-700 text-white" : "bg-amber-500 text-slate-900"
              }`}
            >
              {t.mkCallMic} {micOn ? "✓" : "✗"}
            </button>
            <button
              onClick={toggleCam}
              className={`rounded-full px-4 py-2 text-sm font-medium ${
                camOn ? "bg-slate-700 text-white" : "bg-amber-500 text-slate-900"
              }`}
            >
              {t.mkCallCam} {camOn ? "✓" : "✗"}
            </button>
            {recordCaseId && (
              <button
                onClick={() => (recState === "on" ? void stopRecording() : void startRecording())}
                disabled={recState === "starting"}
                className={`rounded-full px-4 py-2 text-sm font-medium ${
                  recState === "on"
                    ? "bg-red-600 text-white"
                    : "bg-slate-700 text-white hover:bg-slate-600"
                }`}
              >
                ⏺ {recState === "on" ? t.callRecStop : t.callRecBtn}
              </button>
            )}
          </>
        )}
        <button
          onClick={hangUp}
          className="rounded-full bg-red-600 text-white px-5 py-2 text-sm font-bold hover:bg-red-700"
        >
          {t.mkCallEnd}
        </button>
      </div>
    </div>
  );
}
