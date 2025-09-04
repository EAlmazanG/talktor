"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getUserSessions, type UserSessionsResponse } from "@/lib/api";

function formatDateShort(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

function formatDuration(seconds?: number | null): string {
  if (seconds == null || isNaN(seconds as any)) return "—";
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function FeedbackBadge({ has, score }: { has: boolean; score?: number | null }) {
  if (!has) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] md:text-xs bg-gray-200/60 dark:bg-white/10 text-gray-700 dark:text-gray-300">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-400/80" />
        No feedback
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] md:text-xs bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 6L9 17l-5-5" />
      </svg>
      Feedback{typeof score === "number" ? ` • ${score}` : ""}
    </span>
  );
}

export default function LearnPage() {
  const [data, setData] = useState<UserSessionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getUserSessions();
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <div className="flex flex-col gap-4">
      {/* Section header: Session History */}
      <div className="flex items-center">
        <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400">Session History</div>
        <button
          className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          onClick={fetchSessions}
          disabled={loading}
        >
          <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.13-3.36L23 10M1 14l5.37 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <div className="text-sm text-rose-600">{error}</div>}

      {!data && !loading && <div className="text-sm">No sessions to display.</div>}

      {data && (
        <div className="overflow-x-auto rounded-lg">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              <tr className="text-left">
                <th className="py-2.5 pl-3 pr-2">Started</th>
                <th className="py-2.5 pr-2">Duration</th>
                <th className="py-2.5 pr-2">Feedback</th>
                <th className="py-2.5 pr-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {[...data.sessions]
                .sort((a, b) => {
                  const ta = new Date(a.session.started_at || 0).getTime();
                  const tb = new Date(b.session.started_at || 0).getTime();
                  return tb - ta; // latest first
                })
                .map((s) => (
                <tr key={s.session.session_id} className="hover:bg-black/5 dark:hover:bg-white/5">
                  <td className="py-2.5 pl-3 pr-2 whitespace-nowrap">{formatDateShort(s.session.started_at)}</td>
                  <td className="py-2.5 pr-2">{formatDuration(s.session.duration_seconds)}</td>
                  <td className="py-2.5 pr-2">
                    <FeedbackBadge has={!!s.has_feedback} score={s.feedback_score} />
                  </td>
                  <td className="py-2.5 pr-3 text-right">
                    {s.has_feedback ? (
                      <Link
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                        href={`/learn/feedback/${encodeURIComponent(s.session.session_id)}`}
                      >
                        View details
                        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                          <path d="M5 12h14" />
                          <path d="m13 5 7 7-7 7" />
                        </svg>
                      </Link>
                    ) : (
                      <span className="text-xs text-gray-500 dark:text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
