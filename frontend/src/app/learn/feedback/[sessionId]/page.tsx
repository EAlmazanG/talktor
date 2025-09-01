"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getFeedbackSummary, type FeedbackSummaryResponse } from "@/lib/api";

export default function FeedbackSummaryPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = params.sessionId;

  const [summary, setSummary] = useState<FeedbackSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    if (!sessionId) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getFeedbackSummary(sessionId);
        if (mounted) setSummary(res);
      } catch (e: any) {
        if (mounted) setError(e?.message || "Failed to load feedback summary");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [sessionId]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-semibold">Session feedback</h1>
        <span className="font-mono text-xs px-2 py-1 rounded bg-black/5 dark:bg-white/10">{sessionId}</span>
        <button className="ml-auto px-3 py-1.5 rounded-md border" onClick={() => router.back()}>
          Back
        </button>
      </div>

      {loading && <div className="text-sm">Loading...</div>}
      {error && <div className="text-sm text-rose-600">{error}</div>}

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 rounded-md border p-3">
            <div className="font-semibold mb-1">General summary</div>
            <div className="text-sm whitespace-pre-wrap">
              {summary.general_summary || "No summary available."}
            </div>
          </div>
          <div className="rounded-md border p-3">
            <div className="font-semibold mb-2">Scores</div>
            <div className="text-sm">Overall: {summary.overall_score ?? "—"}</div>
            <div className="mt-2 text-xs grid grid-cols-2 gap-x-3 gap-y-1">
              {summary.pillar_scores &&
                Object.entries(summary.pillar_scores).map(([pillar, score]) => (
                  <div key={pillar} className="flex items-center justify-between">
                    <span className="capitalize">{pillar}</span>
                    <span className="font-mono">{score as any}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {!loading && !summary && !error && (
        <div className="text-sm">No summary found for this session.</div>
      )}
    </div>
  );
}
