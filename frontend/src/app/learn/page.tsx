"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getUserSessions, type UserSessionsResponse } from "@/lib/api";

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
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-semibold">Learn</h1>
        <button className="ml-auto px-3 py-1.5 rounded-md border" onClick={fetchSessions} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <div className="text-sm text-rose-600">{error}</div>}

      {!data && !loading && <div className="text-sm">No sessions to display.</div>}

      {data && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2 pr-2">Session</th>
                <th className="py-2 pr-2">Started</th>
                <th className="py-2 pr-2">Ended</th>
                <th className="py-2 pr-2">Duration</th>
                <th className="py-2 pr-2">Messages</th>
                <th className="py-2 pr-2">Feedback</th>
                <th className="py-2 pr-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.sessions.map((s) => (
                <tr key={s.session.session_id} className="border-b hover:bg-black/5 dark:hover:bg-white/5">
                  <td className="py-2 pr-2 font-mono text-xs">{s.session.session_id}</td>
                  <td className="py-2 pr-2">{s.session.started_at || "—"}</td>
                  <td className="py-2 pr-2">{s.session.ended_at || "—"}</td>
                  <td className="py-2 pr-2">{s.session.duration_seconds ?? "—"}s</td>
                  <td className="py-2 pr-2">{s.message_count ?? "—"}</td>
                  <td className="py-2 pr-2">
                    {s.has_feedback ? (
                      <span className="text-emerald-600">yes</span>
                    ) : (
                      <span className="text-amber-600">no</span>
                    )}
                  </td>
                  <td className="py-2 pr-2">
                    <div className="flex gap-2">
                      <Link
                        className="px-3 py-1 rounded-md border text-xs"
                        href={`/learn/feedback/${encodeURIComponent(s.session.session_id)}`}
                      >
                        View summary
                      </Link>
                    </div>
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
