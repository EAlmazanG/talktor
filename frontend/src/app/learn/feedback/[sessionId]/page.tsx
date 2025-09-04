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
        <h1 className="text-xl font-semibold">Session feedback</h1>
        <span className="font-mono text-xs px-2 py-1 rounded bg-black/5 dark:bg-white/10">{sessionId}</span>
        <button className="ml-auto px-3 py-1.5 rounded-md border" onClick={() => router.replace("/learn")}>
          Back
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
