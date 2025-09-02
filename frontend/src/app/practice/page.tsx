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
  const [input, setInput] = useState("");
  const [userTranscript, setUserTranscript] = useState("");
  const [aiTranscript, setAiTranscript] = useState("");
  const clientRef = useRef<RealtimeClient | null>(null);
  const micRef = useRef<MicStreamController | null>(null);
  const playerRef = useRef<AiAudioPlayer | null>(null);
  const [ended, setEnded] = useState(false);
  const [feedbackSummary, setFeedbackSummary] = useState<string | null>(null);

  const canStart = useMemo(() => !connecting && !connected && !sessionId, [connecting, connected, sessionId]);
  const canSend = useMemo(() => connected && !ended, [connected, ended]);
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
    setInput("");
    setUserTranscript("");
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
        onUserDelta: (d) => setUserTranscript((prev) => prev + d),
        onUserCompleted: (t) => setUserTranscript((prev) => (prev.endsWith("\n") ? prev : prev + "\n") + t + "\n"),
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

  const handleSend = () => {
    if (!clientRef.current || !input.trim()) return;
    clientRef.current.sendText(input.trim());
    setInput("");
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
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <button
          className="px-4 py-2 rounded-md bg-emerald-600 text-white disabled:opacity-50"
          onClick={handleStart}
          disabled={!canStart}
        >
          Start Conversation
        </button>
        <button
          className="px-4 py-2 rounded-md bg-rose-600 text-white disabled:opacity-50"
          onClick={handleEnd}
          disabled={!canEnd}
        >
          End Conversation
        </button>
        <button
          className="px-3 py-2 rounded-md border ml-auto"
          onClick={reset}
        >
          Reset
        </button>
      </div>

      <div className="text-sm text-black/70 dark:text-white/70 grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <div className="font-semibold">Status</div>
          <div className="text-xs">Session: {sessionId ?? "—"}</div>
          <div className="text-xs">WS: {connected ? "connected" : connecting ? "connecting" : "disconnected"}</div>
          <div className="text-xs">Mic: {micRef.current ? "on" : "off"}</div>
          <div className="text-xs">Ended: {ended ? "yes" : "no"}</div>
          {error && <div className="text-xs text-rose-600">{error}</div>}
        </div>
        <div className="space-y-1">
          <div className="font-semibold">Actions</div>
          <div className="flex gap-2">
            <input
              className="flex-1 px-3 py-2 rounded-md border bg-transparent"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={!canSend}
            />
            <button
              className="px-4 py-2 rounded-md border"
              onClick={handleSend}
              disabled={!canSend || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="font-semibold mb-1">You</div>
          <pre className="p-3 rounded-md border overflow-auto whitespace-pre-wrap text-sm min-h-48">{userTranscript || "(waiting...)"}</pre>
        </div>
        <div>
          <div className="font-semibold mb-1">Talktor</div>
          <pre className="p-3 rounded-md border overflow-auto whitespace-pre-wrap text-sm min-h-48">{aiTranscript || "(waiting...)"}</pre>
        </div>
      </div>

      {ended && (
        <div className="rounded-md border p-3">
          <div className="font-semibold mb-1">Feedback summary</div>
          <div className="text-sm whitespace-pre-wrap">
            {feedbackSummary ? feedbackSummary : "No summary available yet."}
          </div>
        </div>
      )}
    </div>
  );
}
