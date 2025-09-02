"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { endConversation, getFeedbackSummary, startConversation, type FeedbackSummaryResponse } from "@/lib/api";
import { openRealtimeWebSocket, type RealtimeClient } from "@/lib/ws";
import { startMicStreaming, createAiAudioPlayer, type MicStreamController, type AiAudioPlayer } from "@/lib/audio";

export default function PracticePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [wsUrl, setWsUrl] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiMessage, setAiMessage] = useState("");
  const clientRef = useRef<RealtimeClient | null>(null);
  const micRef = useRef<MicStreamController | null>(null);
  const playerRef = useRef<AiAudioPlayer | null>(null);
  const [ended, setEnded] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackSummaryResponse | null>(null);

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
    setAiMessage("");
    setEnded(false);
    setFeedback(null);
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
    setAiMessage("");
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
        // Only show the latest completed AI message (no streaming text)
        onUserDelta: () => {},
        onUserCompleted: () => {},
        onAiDelta: () => {},
        onAiCompleted: (t) => setAiMessage(t),
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
            setFeedback(summary || null);
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
        setFeedback(summary || null);
      } catch (_) {}
    } catch (e: any) {
      setError(e?.message || "Failed to end conversation");
    }
  };

  return (
    <div className="relative min-h-[70vh] flex flex-col items-center justify-center">
      {/* Status panel (bottom-right, minimal) */}
      <div className="fixed bottom-4 right-4 text-[11px] md:text-xs text-gray-500 dark:text-gray-400 opacity-80">
        <div className="flex items-center gap-2">
          <span>WS: {connected ? "connected" : connecting ? "connecting" : "disconnected"}</span>
          <span>•</span>
          <span>Mic: {micRef.current ? "on" : "off"}</span>
          <span>•</span>
          <span>Ended: {ended ? "yes" : "no"}</span>
        </div>
        <div className="font-mono opacity-70">Session: {sessionId ?? "—"}</div>
        {error && <div className="text-rose-500">{error}</div>}
      </div>

      {/* Controls */}
      <div className="mb-6 flex items-center gap-3">
        <button
          className="px-5 py-2.5 rounded-full bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          onClick={handleStart}
          disabled={!canStart}
        >
          Start Conversation
        </button>
        <button
          className="px-5 py-2.5 rounded-full bg-rose-600 text-white text-sm font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          onClick={handleEnd}
          disabled={!canEnd}
        >
          End Conversation
        </button>
        <button
          className="px-4 py-2 rounded-full text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white underline-offset-4 hover:underline transition-colors"
          onClick={reset}
        >
          Reset
        </button>
      </div>

      {/* Centered AI message (clean, no frames) */}
      <div className="w-full max-w-3xl px-4">
        <div className="text-center text-xl md:text-2xl font-light leading-relaxed text-gray-900 dark:text-gray-100">
          {aiMessage || (connected ? "Listening..." : "Press Start to begin")}
        </div>
      </div>

      {/* Feedback after end (clean, spaced, includes scores) */}
      {ended && (
        <div className="mt-10 w-full max-w-3xl px-4 space-y-4">
          <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Feedback</div>
          {feedback ? (
            <>
              <div className="text-base font-light whitespace-pre-wrap text-gray-900 dark:text-gray-100">
                {feedback.general_summary || "No summary available."}
              </div>
              {(feedback.overall_score != null || feedback.pillar_scores) && (
                <div className="space-y-2">
                  {feedback.overall_score != null && (
                    <div className="text-sm text-gray-600 dark:text-gray-300">
                      Overall score: <span className="font-medium text-gray-900 dark:text-gray-100">{feedback.overall_score}</span>
                    </div>
                  )}
                  {feedback.pillar_scores && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-1 gap-x-4 text-sm text-gray-600 dark:text-gray-300">
                      {Object.entries(feedback.pillar_scores).map(([pillar, score]) => (
                        <div key={pillar} className="flex items-center justify-between">
                          <span className="capitalize">{pillar}</span>
                          <span className="font-mono text-gray-900 dark:text-gray-100">{score as any}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div>
                <Link
                  href={`/progress/${encodeURIComponent(sessionId || feedback.session_id)}`}
                  className="inline-flex items-center px-4 py-2 rounded-full border text-xs font-medium hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                >
                  View details
                </Link>
              </div>
            </>
          ) : (
            <div className="text-sm font-light text-gray-600 dark:text-gray-300">No summary available yet.</div>
          )}
        </div>
      )}
    </div>
  );
}
