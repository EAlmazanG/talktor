"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { getFeedbackSummary, type FeedbackSummaryResponse } from "@/lib/api";

export default function ProgressDetailsPage() {
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
        if (mounted) setSummary(res || null);
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
    <div className="mx-auto w-full max-w-3xl px-4 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">Progress details</h1>
        <span className="font-mono text-xs opacity-70">{sessionId}</span>
        <div className="ml-auto flex items-center gap-2">
          <Link href="/progress" className="text-xs underline underline-offset-4 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
            Back to Progress
          </Link>
          <button onClick={() => router.refresh()} className="text-xs underline underline-offset-4 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
            Refresh
          </button>
        </div>
      </div>

      {loading && <div className="text-sm">Loading...</div>}
      {error && <div className="text-sm text-rose-600">{error}</div>}

      {summary && (
        <div className="space-y-6">
          <section className="space-y-2">
            <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">General summary</div>
            <div className="text-base font-light whitespace-pre-wrap text-gray-900 dark:text-gray-100">
              {summary.general_summary || "No summary available."}
            </div>
          </section>

          {(summary.overall_score != null || summary.pillar_scores) && (
            <section className="space-y-3">
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Scores</div>
              {summary.overall_score != null && (
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  Overall score: <span className="font-medium text-gray-900 dark:text-gray-100">{summary.overall_score}</span>
                </div>
              )}
              {summary.pillar_scores && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-2 gap-x-6 text-sm text-gray-600 dark:text-gray-300">
                  {Object.entries(summary.pillar_scores).map(([pillar, score]) => (
                    <div key={pillar} className="flex items-center justify-between">
                      <span className="capitalize">{pillar}</span>
                      <span className="font-mono text-gray-900 dark:text-gray-100">{score as any}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      )}

      {!loading && !summary && !error && (
        <div className="text-sm font-light text-gray-600 dark:text-gray-300">No summary found for this session.</div>
      )}
    </div>
  );
}
