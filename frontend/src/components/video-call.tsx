"use client";

/**
 * SOS video/audio call overlay (LiveKit). Used by both sides of a claimed
 * marketplace case: the lawyer (Tregu) and the citizen (/rasti-im).
 * The server decides whether video is enabled; when it is not, we show a
 * friendly note instead of a broken call.
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
}: {
  fetchGrant: () => Promise<CallGrant>;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const [phase, setPhase] = useState<"connecting" | "waiting" | "live" | "off" | "error">(
    "connecting"
  );
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const roomRef = useRef<Room | null>(null);
  const localRef = useRef<HTMLDivElement>(null);
  const remoteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
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
      room.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    roomRef.current?.disconnect();
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 flex flex-col items-center justify-center p-4">
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
      <div className="flex items-center gap-3 mt-4">
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
