"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getFeedback, type FeedbackResponse } from "@/lib/api";
import FeedbackDetails from "@/components/FeedbackDetails";

export default function FeedbackSummaryPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = params.sessionId;

  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    if (!sessionId) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getFeedback(sessionId);
        if (mounted) setFeedback(res || null);
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
        <button
          className="ml-auto inline-flex items-center gap-2 rounded-lg border border-black/10 dark:border-white/10 bg-transparent hover:bg-black/5 dark:hover:bg-white/5 px-3 py-1.5 text-sm text-gray-800 dark:text-gray-100"
          onClick={() => router.replace("/learn")}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
            aria-hidden
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          <span>Back</span>
        </button>
      </div>

      {loading && <div className="text-sm">Loading...</div>}
      {error && <div className="text-sm text-rose-600">{error}</div>}

      {feedback && <FeedbackDetails feedback={feedback} />}

      {!loading && !feedback && !error && (
        <div className="text-sm">No feedback found for this session.</div>
      )}
    </div>
  );
}
