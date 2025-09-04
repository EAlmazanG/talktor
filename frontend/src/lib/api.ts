// API helpers for Talktor frontend
// All code and comments must be in English

export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  return base.replace(/\/$/, "");
}

export function getUserId(): string {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem("userId");
    if (stored && stored.trim().length > 0) return stored.trim();
  }
  return "default_user";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path}`;
  const headers = new Headers(init?.headers || {});
  headers.set("Content-Type", "application/json");
  headers.set("X-User-Id", getUserId());

  const res = await fetch(url, { ...init, headers });
  if (!res.ok) {
    let payload: any = undefined;
    try {
      payload = await res.json();
    } catch (_) {
      // ignore
    }
    throw new Error(payload?.detail || payload?.message || `HTTP ${res.status}`);
  }
  // Some endpoints may return empty responses
  const text = await res.text();
  return text ? (JSON.parse(text) as T) : (undefined as unknown as T);
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
}

// Specific API wrappers
export interface StartConversationResponse {
  session_id: string;
  status: string;
  websocket_url: string; // may be a path e.g. "/api/v1/conversations/{id}/realtime"
}

export interface FeedbackSummaryResponse {
  session_id: string;
  overall_score?: number;
  general_summary?: string;
  pillar_scores?: Record<string, number>;
  created_at?: string;
}

// Detailed feedback response matching backend schemas/feedback.py
export interface PillarFeedback {
  score?: number;
  summary?: string;
  errors: string[];
  suggestions: string[];
}

export interface FeedbackResponse {
  session_id: string;
  overall_score?: number;
  general_feedback?: string;
  general_summary?: string;
  general_errors: string[];
  general_suggestions: string[];
  pronunciation: PillarFeedback;
  fluency: PillarFeedback;
  grammar: PillarFeedback;
  expressions: PillarFeedback;
  vocabulary: PillarFeedback;
  comprehension: PillarFeedback;
  created_at: string;
  generated_by: string;
}

export interface UserSessionsResponse {
  sessions: Array<{
    session: {
      session_id: string;
      user_id: string;
      agent_type: string;
      mode?: string | null;
      duration_seconds?: number | null;
      started_at?: string | null;
      ended_at?: string | null;
      status?: string | null;
    };
    message_count?: number;
    has_feedback?: boolean;
    feedback_score?: number | null;
  }>;
  total: number;
  page: number;
  page_size: number;
}

export function startConversation(userId?: string) {
  const uid = userId || getUserId();
  return apiPost<StartConversationResponse>("/api/v1/conversations/start", { user_id: uid });
}

export function endConversation(sessionId: string) {
  return apiPost(`/api/v1/conversations/${sessionId}/end`, { force_feedback: false });
}

export function getFeedbackSummary(sessionId: string) {
  return apiGet<FeedbackSummaryResponse>(`/api/v1/feedback/${sessionId}/summary`);
}

export function getFeedback(sessionId: string) {
  return apiGet<FeedbackResponse>(`/api/v1/feedback/${sessionId}`);
}

export function getUserSessions(userId?: string) {
  const uid = userId || getUserId();
  return apiGet<UserSessionsResponse>(`/api/v1/users/${encodeURIComponent(uid)}/sessions`);
}
