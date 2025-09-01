// WebSocket helper for Talktor realtime conversations
// All code and comments must be in English

export type RealtimeListeners = {
  onOpen?: () => void;
  onClose?: (ev: CloseEvent) => void;
  onError?: (ev: Event) => void;
  onUserDelta?: (delta: string) => void;
  onUserCompleted?: (text: string) => void;
  onAiDelta?: (delta: string) => void;
  onAiCompleted?: (text: string) => void;
  onPlaybackClear?: (reason?: string) => void;
  onEnded?: (payload: any) => void;
  onBinaryAudio?: (bytes: ArrayBuffer) => void;
  onGeneric?: (evt: any) => void; // fallback for unknown events
};

function buildWsUrl(websocketUrl: string): string {
  // If already a full ws:// or wss:// URL, return as is
  if (/^wss?:\/\//i.test(websocketUrl)) return websocketUrl;

  // If it's a path like "/api/v1/conversations/{id}/realtime",
  // derive from NEXT_PUBLIC_API_BASE_URL and switch scheme to ws/wss.
  const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
  const base = new URL(apiBase);
  const wsProtocol = base.protocol === "https:" ? "wss:" : "ws:";
  return `${wsProtocol}//${base.host}${websocketUrl}`;
}

export type RealtimeClient = {
  ws: WebSocket;
  sendJson: (obj: any) => void;
  sendText: (text: string) => void;
  end: () => void;
  close: () => void;
};

export function openRealtimeWebSocket(
  websocketUrl: string,
  listeners: RealtimeListeners
): RealtimeClient {
  const url = buildWsUrl(websocketUrl);
  const ws = new WebSocket(url);

  ws.binaryType = "arraybuffer";

  ws.onopen = () => listeners.onOpen?.();
  ws.onclose = (ev) => listeners.onClose?.(ev);
  ws.onerror = (ev) => listeners.onError?.(ev);
  ws.onmessage = (ev) => {
    // Binary AI audio frames arrive as ArrayBuffer
    if (ev.data instanceof ArrayBuffer) {
      listeners.onBinaryAudio?.(ev.data);
      return;
    }
    // Blob → convert to text
    if (ev.data instanceof Blob) {
      (ev.data as Blob)
        .text()
        .then((text) => handleJsonMessage(text, listeners))
        .catch(() => {});
      return;
    }
    // String JSON
    if (typeof ev.data === "string") {
      handleJsonMessage(ev.data as string, listeners);
    }
  };

  function handleJsonMessage(text: string, ls: RealtimeListeners) {
    try {
      const evt = JSON.parse(text);
      const t = evt?.type as string | undefined;
      if (!t) {
        ls.onGeneric?.(evt);
        return;
      }
      switch (t) {
        case "user_transcript.delta":
          ls.onUserDelta?.(evt.delta ?? "");
          break;
        case "user_transcript.completed":
          ls.onUserCompleted?.(evt.transcript ?? "");
          break;
        case "ai_transcript.delta":
          ls.onAiDelta?.(evt.delta ?? "");
          break;
        case "ai_transcript.completed":
          ls.onAiCompleted?.(evt.transcript ?? "");
          break;
        case "playback.clear":
          ls.onPlaybackClear?.(evt.reason);
          break;
        case "ended":
          ls.onEnded?.(evt);
          break;
        default:
          ls.onGeneric?.(evt);
          break;
      }
    } catch {
      // ignore malformed
    }
  }

  return {
    ws,
    sendJson: (obj: any) => ws.readyState === WebSocket.OPEN && ws.send(JSON.stringify(obj)),
    sendText: (text: string) =>
      ws.readyState === WebSocket.OPEN && ws.send(JSON.stringify({ type: "input_text", text })),
    end: () => ws.readyState === WebSocket.OPEN && ws.send(JSON.stringify({ type: "end" })),
    close: () => ws.close(),
  };
}
