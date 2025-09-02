"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { endConversation, getFeedbackSummary, startConversation } from "@/lib/api";
import { openRealtimeWebSocket, type RealtimeClient } from "@/lib/ws";
import { startMicStreaming, createAiAudioPlayer, type MicStreamController, type AiAudioPlayer } from "@/lib/audio";

export default function PracticePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [wsUrl, setWsUrl] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiTranscript, setAiTranscript] = useState("");
  const clientRef = useRef<RealtimeClient | null>(null);
  const micRef = useRef<MicStreamController | null>(null);
  const playerRef = useRef<AiAudioPlayer | null>(null);
  const [ended, setEnded] = useState(false);
  const [feedbackSummary, setFeedbackSummary] = useState<string | null>(null);

  const canStart = useMemo(() => !connecting && !connected && !sessionId, [connecting, connected, sessionId]);
  const canEnd = useMemo(() => connected && !!sessionId && !ended, [connected, sessionId, ended]);

  const reset = useCallback(() => {
    clientRef.current?.close();
    clientRef.current = null;
    try { micRef.current?.stop(); } catch {}
    micRef.current = null;
    if (playerRef.current) {
      playerRef.current.clear();
      // do not close the AudioContext to allow reuse; but we can close to free resources
      // void playerRef.current.close();
    }
    setSessionId(null);
    setWsUrl(null);
    setConnecting(false);
    setConnected(false);
    setError(null);
    setAiTranscript("");
    setEnded(false);
    setFeedbackSummary(null);
  }, []);

  useEffect(() => {
    return () => {
      clientRef.current?.close();
      try { micRef.current?.stop(); } catch {}
      micRef.current = null;
      if (playerRef.current) {
        // Close audio player resources on unmount
        void playerRef.current.close();
        playerRef.current = null;
      }
    };
  }, []);

  const handleStart = async () => {
    setError(null);
    setConnecting(true);
    try {
      const res = await startConversation();
      setSessionId(res.session_id);
      setWsUrl(res.websocket_url);

      // Ensure an AI audio player exists for playback
      if (!playerRef.current) {
        playerRef.current = createAiAudioPlayer();
      } else {
        playerRef.current.clear();
      }

      const client = openRealtimeWebSocket(res.websocket_url, {
        onOpen: () => {
          setConnected(true);
          // Start microphone streaming once the socket is open
          void startMicStreaming(client)
            .then((ctrl) => {
              micRef.current = ctrl;
            })
            .catch((e: any) => {
              setError(`Microphone error: ${e?.message || "permission or device issue"}`);
            });
        },
        onClose: () => {
          setConnected(false);
          try { micRef.current?.stop(); } catch {}
          micRef.current = null;
        },
        onError: () => setError("WebSocket error"),
        // Do not render user transcript in this UX
        onUserDelta: () => {},
        onUserCompleted: () => {},
        onAiDelta: (d) => setAiTranscript((prev) => prev + d),
        onAiCompleted: (t) => setAiTranscript((prev) => (prev.endsWith("\n") ? prev : prev + "\n") + t + "\n"),
        onPlaybackClear: () => {
          // Clear buffered AI audio when barge-in or end requested
          playerRef.current?.clear();
        },
        onEnded: async () => {
          setEnded(true);
          try { micRef.current?.stop(); } catch {}
          micRef.current = null;
          // Try to fetch feedback summary if available
          try {
            const sid = res.session_id;
            const summary = await getFeedbackSummary(sid);
            setFeedbackSummary(summary?.general_summary || "");
          } catch (_) {
            // ignore
          }
        },
        onBinaryAudio: (bytes) => {
          // Feed AI PCM16 bytes for playback
          playerRef.current?.feedPcm16(bytes);
        },
        onGeneric: () => {},
      });

      clientRef.current = client;
    } catch (e: any) {
      setError(e?.message || "Failed to start conversation");
    } finally {
      setConnecting(false);
    }
  };

  const handleEnd = async () => {
    if (!clientRef.current || !sessionId) return;
    try {
      try { micRef.current?.stop(); } catch {}
      micRef.current = null;
      clientRef.current.end();
      await endConversation(sessionId);
      setEnded(true);
      // Also refetch summary after explicit end
      try {
        const summary = await getFeedbackSummary(sessionId);
        setFeedbackSummary(summary?.general_summary || "");
      } catch (_) {}
    } catch (e: any) {
      setError(e?.message || "Failed to end conversation");
    }
  };

  return (
    <div className="relative min-h-[70vh] flex flex-col items-center justify-center">
      {/* Status panel (top-right corner) */}
      <div className="fixed top-4 right-4 rounded-xl border bg-white/70 dark:bg-black/30 backdrop-blur px-4 py-3 text-xs shadow-sm space-y-1">
        <div className="font-semibold">Status</div>
        <div>Session: <span className="font-mono">{sessionId ?? "—"}</span></div>
        <div>WS: {connected ? "connected" : connecting ? "connecting" : "disconnected"}</div>
        <div>Mic: {micRef.current ? "on" : "off"}</div>
        <div>Ended: {ended ? "yes" : "no"}</div>
        {error && <div className="text-rose-600">{error}</div>}
      </div>

      {/* Controls */}
      <div className="mb-6 flex items-center gap-3">
        <button
          className="px-6 py-3 rounded-full bg-emerald-600 text-white text-sm md:text-base shadow hover:shadow-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition"
          onClick={handleStart}
          disabled={!canStart}
        >
          🚀 Start Conversation
        </button>
        <button
          className="px-6 py-3 rounded-full bg-rose-600 text-white text-sm md:text-base shadow hover:shadow-md hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition"
          onClick={handleEnd}
          disabled={!canEnd}
        >
          ⏹ End Conversation
        </button>
        <button
          className="px-4 py-2 rounded-full border bg-white/50 dark:bg-white/10 text-xs shadow-sm hover:bg-white/70 transition"
          onClick={reset}
        >
          Reset
        </button>
      </div>

      {/* Centered AI transcript */}
      <div className="w-full max-w-2xl">
        <div className="rounded-2xl border bg-white/70 dark:bg-black/30 backdrop-blur p-5 shadow-sm">
          <div className="text-sm font-semibold mb-2">Talktor</div>
          <div className="text-sm whitespace-pre-wrap min-h-40 leading-relaxed">
            {aiTranscript || (connected ? "(Listening...)" : "(Press Start to begin)")}
          </div>
        </div>
      </div>

      {/* Feedback summary after end */}
      {ended && (
        <div className="mt-6 w-full max-w-2xl">
          <div className="rounded-2xl border p-5 bg-white/80 dark:bg-black/30 backdrop-blur">
            <div className="text-sm font-semibold mb-2">Feedback summary</div>
            <div className="text-sm whitespace-pre-wrap">
              {feedbackSummary ? feedbackSummary : "No summary available yet."}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
