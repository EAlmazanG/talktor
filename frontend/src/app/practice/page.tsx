"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { endConversation, getFeedbackSummary, startConversation, type FeedbackSummaryResponse } from "@/lib/api";
import { openRealtimeWebSocket, type RealtimeClient } from "@/lib/ws";
import { startMicStreaming, createAiAudioPlayer, type MicStreamController, type AiAudioPlayer } from "@/lib/audio";
import VoiceDots from "@/components/VoiceDots";

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
  const typingTimerRef = useRef<number | null>(null);
  const levelTimerRef = useRef<number | null>(null);
  const levelSmoothRef = useRef(0);
  const [aiLevel, setAiLevel] = useState(0);

  const canStart = useMemo(() => !connecting && !connected && !sessionId, [connecting, connected, sessionId]);
  const canEnd = useMemo(() => connected && !!sessionId && !ended, [connected, sessionId, ended]);

  const controlsClass = useMemo(() => {
    const base = "flex items-center gap-3 transition-all duration-300 ease-out";
    if (connecting || connected) {
      return base + " -translate-y-2 md:-translate-y-3 mb-16 md:mb-20";
    }
    return base + " mb-8";
  }, [connecting, connected]);

  const stopTyping = () => {
    if (typingTimerRef.current != null) {
      window.clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }
  };

  const startTyping = (text: string) => {
    stopTyping();
    setAiMessage("");
    let i = 0;
    const step = 2; // fast typing: 2 chars per tick
    typingTimerRef.current = window.setInterval(() => {
      i += step;
      setAiMessage(text.slice(0, i));
      if (i >= text.length) {
        stopTyping();
      }
    }, 12);
  };

  const stopLevelTimer = () => {
    if (levelTimerRef.current != null) {
      window.clearInterval(levelTimerRef.current);
      levelTimerRef.current = null;
    }
  };

  const startLevelTimer = () => {
    stopLevelTimer();
    levelSmoothRef.current = 0;
    levelTimerRef.current = window.setInterval(() => {
      const lv = playerRef.current?.getLevel?.() ?? 0;
      // Exponential smoothing to avoid flicker
      levelSmoothRef.current = levelSmoothRef.current * 0.8 + lv * 0.2;
      setAiLevel(levelSmoothRef.current);
    }, 33); // ~30fps
  };

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
    stopTyping();
    stopLevelTimer();
    levelSmoothRef.current = 0;
    setAiLevel(0);
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
      stopLevelTimer();
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
      // Start polling AI playback level for visualization
      startLevelTimer();

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
          stopLevelTimer();
        },
        onError: () => setError("WebSocket error"),
        // Only show the latest completed AI message (no streaming text)
        onUserDelta: () => {},
        onUserCompleted: () => {},
        onAiDelta: () => {},
        onAiCompleted: (t) => startTyping(t),
        onPlaybackClear: () => {
          // Clear buffered AI audio when barge-in or end requested
          playerRef.current?.clear();
          // Drop level immediately
          levelSmoothRef.current = 0;
          setAiLevel(0);
        },
        onEnded: async () => {
          setEnded(true);
          try { micRef.current?.stop(); } catch {}
          micRef.current = null;
          stopLevelTimer();
          // Farewell message with subtle fade-up
          startTyping("See you soon!");
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
      // Show farewell immediately
      startTyping("See you soon!");
      clientRef.current.end();
      await endConversation(sessionId);
      setEnded(true);
      stopLevelTimer();
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
      {/* Large centered Talktor logo above controls */}
      <div className="w-full flex items-center justify-center mb-8 md:mb-10">
        {connecting || connected ? (
          <VoiceDots level={aiLevel} />
        ) : (
          <Image
            src="/assets/icons/talktor.png"
            alt="Talktor"
            width={200}
            height={200}
            priority
          />
        )}
      </div>

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

      {/* Controls: Start + End centered; Reset immediately to the right (does not affect centering) */}
      <div className="w-full flex items-center justify-center">
        <div className={controlsClass + " justify-center relative flex-nowrap"}>
          <div className="inline-flex items-center gap-3 flex-nowrap">
            <button
              className={`px-5 py-2.5 rounded-full text-sm transition-colors ${
                canStart
                  ? "bg-emerald-600 text-white hover:bg-emerald-700 font-semibold"
                  : "bg-gray-300 text-gray-500 font-normal"
              } disabled:cursor-not-allowed`}
              onClick={handleStart}
              disabled={!canStart}
            >
              Start Conversation
            </button>
            <button
              className={`px-5 py-2.5 rounded-full text-sm transition-colors ${
                canEnd
                  ? "bg-rose-600 text-white hover:bg-rose-700 font-semibold"
                  : "bg-gray-300 text-gray-500 font-normal"
              } disabled:cursor-not-allowed`}
              onClick={handleEnd}
              disabled={!canEnd}
            >
              End Conversation
            </button>
          </div>
          <button
            className="px-4 py-2 rounded-full text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white underline-offset-4 hover:underline transition-colors absolute left-full ml-3 top-1/2 -translate-y-1/2"
            onClick={reset}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Centered AI message (clean, no frames) */}
      <div className="w-full max-w-3xl px-4">
        <div
          className={
            "text-center text-xl md:text-2xl font-light leading-relaxed text-gray-900 dark:text-gray-100 transition-all duration-300 ease-out " +
            (ended ? "opacity-70 -translate-y-1 md:-translate-y-2" : "")
          }
        >
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
