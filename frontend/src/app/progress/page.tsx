"use client";

import React, { useEffect, useMemo, useState } from "react";
import MiniLineChart, { type ChartPoint } from "@/components/MiniLineChart";
import { getAllUserSessions, getFeedbackSummary, type UserSessionsResponse, type FeedbackSummaryResponse } from "@/lib/api";

type PillarKey = "pronunciation" | "fluency" | "grammar" | "expressions" | "vocabulary" | "comprehension";

function toDayKey(d: Date) {
  const y = d.getFullYear();
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const dd = `${d.getDate()}`.padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

// Convert a YYYY-MM-DD key into a local-midnight Date to align with chart day ticks
function dayKeyToLocalDate(key: string): Date {
  const [ys, ms, ds] = key.split("-");
  const y = parseInt(ys, 10);
  const m = parseInt(ms, 10);
  const d = parseInt(ds, 10);
  return new Date(y, (m || 1) - 1, d || 1);
}

// Compute a [start,end] domain for the last N days inclusive, aligned to local midnight
function lastNDaysDomain(n: number): [Date, Date] {
  const now = new Date();
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const start = new Date(end.getFullYear(), end.getMonth(), end.getDate() - Math.max(0, n - 1));
  return [start, end];
}

function parseISO(x?: string | null): Date | null {
  if (!x) return null;
  const d = new Date(x);
  return isNaN(d.getTime()) ? null : d;
}

export default function ProgressPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<UserSessionsResponse["sessions"]>([]);
  const [summaries, setSummaries] = useState<Record<string, FeedbackSummaryResponse>>({});
  // Day range filter for all charts (default: last 14 days)
  const [rangeDays, setRangeDays] = useState(14);

  // Load sessions and summaries (reusable so we can wire a Refresh button)
  const fetchProgress = async (isMounted?: () => boolean) => {
    setLoading(true);
    setError(null);
    try {
      // 1) Fetch sessions (all pages)
      const res = await getAllUserSessions();
      if (isMounted && !isMounted()) return;
      const filtered = (res.sessions || []).filter((row) => {
        const dur = row.session?.duration_seconds || 0;
        return dur >= 30 && row.has_feedback;
      });
      setSessions(filtered);

      // 2) Fetch summaries for qualifying sessions in parallel
      const pairs = await Promise.all(
        filtered.map(async (row) => {
          try {
            const sId = row.session.session_id;
            const s = await getFeedbackSummary(sId);
            return [sId, s] as const;
          } catch (_) {
            return null;
          }
        })
      );
      if (isMounted && !isMounted()) return;
      const map: Record<string, FeedbackSummaryResponse> = {};
      for (const p of pairs) if (p) map[p[0]] = p[1];
      setSummaries(map);
    } catch (e: any) {
      if (isMounted && !isMounted()) return;
      setError(e?.message || "Failed to load progress");
    } finally {
      if (isMounted && !isMounted()) return;
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    void fetchProgress(() => mounted);
    return () => {
      mounted = false;
    };
  }, []);

  const { overallPoints, pillarPoints } = useMemo(() => {
    const dayValuesOverall: Record<string, number[]> = {};
    const dayValuesPillars: Record<PillarKey, Record<string, number[]>> = {
      pronunciation: {},
      fluency: {},
      grammar: {},
      expressions: {},
      vocabulary: {},
      comprehension: {},
    };

    for (const row of sessions) {
      const s = row.session;
      const sid = s.session_id;
      const sum = summaries[sid];
      if (!sum) continue;
      const when = parseISO(s.started_at) || parseISO(sum.created_at);
      if (!when) continue;
      const key = toDayKey(when);

      if (Number.isFinite(sum.overall_score as any)) {
        (dayValuesOverall[key] ||= []).push((sum.overall_score as number) || 0);
      }
      const ps = sum.pillar_scores || {};
      (Object.keys(dayValuesPillars) as PillarKey[]).forEach((k) => {
        const v = (ps as any)[k];
        if (Number.isFinite(v)) {
          (dayValuesPillars[k][key] ||= []).push(v as number);
        }
      });
    }

    const averageMapToPoints = (m: Record<string, number[]>) => {
      return Object.entries(m)
        .map(([k, arr]) => ({ date: dayKeyToLocalDate(k), value: arr.reduce((a, b) => a + b, 0) / Math.max(1, arr.length) }))
        .sort((a, b) => a.date.getTime() - b.date.getTime());
    };

    const overall = averageMapToPoints(dayValuesOverall);
    const pillars: Record<PillarKey, ChartPoint[]> = {
      pronunciation: averageMapToPoints(dayValuesPillars.pronunciation),
      fluency: averageMapToPoints(dayValuesPillars.fluency),
      grammar: averageMapToPoints(dayValuesPillars.grammar),
      expressions: averageMapToPoints(dayValuesPillars.expressions),
      vocabulary: averageMapToPoints(dayValuesPillars.vocabulary),
      comprehension: averageMapToPoints(dayValuesPillars.comprehension),
    };
    return { overallPoints: overall, pillarPoints: pillars };
  }, [sessions, summaries]);

  // Visible window: last N days including today (local time)
  const [xStart, xEnd] = useMemo(() => lastNDaysDomain(rangeDays), [rangeDays]);
  const inWindow = (p: ChartPoint) => {
    const t = p.date.getTime();
    return t >= xStart.getTime() && t <= xEnd.getTime();
  };
  const overallWindow = useMemo(() => overallPoints.filter(inWindow), [overallPoints, xStart.getTime(), xEnd.getTime()]);
  const pillarsWindow = useMemo(() => ({
    pronunciation: pillarPoints.pronunciation.filter(inWindow),
    fluency: pillarPoints.fluency.filter(inWindow),
    grammar: pillarPoints.grammar.filter(inWindow),
    expressions: pillarPoints.expressions.filter(inWindow),
    vocabulary: pillarPoints.vocabulary.filter(inWindow),
    comprehension: pillarPoints.comprehension.filter(inWindow),
  }), [pillarPoints, xStart.getTime(), xEnd.getTime()]);

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6 space-y-6">
      <div className="flex items-center mb-3 md:mb-4">
        <div className="inline-flex items-center gap-2 rounded-full bg-black/5 dark:bg-white/10 px-2.5 py-1 text-[11px] md:text-xs font-medium uppercase tracking-wide text-gray-700 dark:text-gray-200">
          <span className="h-1.5 w-1.5 rounded-full bg-gray-500/60 dark:bg-gray-300/60" />
          <span>Overall</span>
        </div>
        {/* Right-justified filters + Refresh */}
        <div className="ml-auto inline-flex items-center">
          <div className="inline-flex items-center gap-1">
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                className={`px-2.5 py-1 rounded-full text-[11px] md:text-xs border border-black/10 dark:border-white/10 transition-colors ${
                  rangeDays === d ? "bg-black/10 dark:bg-white/10" : "hover:bg-black/5 dark:hover:bg-white/10"
                }`}
                aria-pressed={rangeDays === d}
                onClick={() => setRangeDays(d)}
              >
                {d}d
              </button>
            ))}
          </div>
          <button
            className="ml-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            onClick={() => fetchProgress()}
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
      </div>

      {error && <div className="text-sm text-rose-600">{error}</div>}

      {/* Overall on top */}
      <section>
        <MiniLineChart
          title="Overall evolution"
          points={overallWindow}
          yDomain={[0, 10]}
          xDomain={[xStart, xEnd]}
          className="text-gray-700 dark:text-gray-300"
          heightPx={260}
          autoY={false}
          yPadding={0}
          minYRange={0.02}
          axisMode="labels"
          axisOpacity={0.05}
          paddingOverrides={{ left: 44, right: 44 }}
        />
      </section>

      <div className="inline-flex items-center gap-2 rounded-full bg-black/5 dark:bg-white/10 px-2.5 py-1 text-[11px] md:text-xs font-medium uppercase tracking-wide text-gray-700 dark:text-gray-200 mb-2 md:mb-3">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-500/60 dark:bg-gray-300/60" />
        <span>Pillars</span>
      </div>

      {/* Pillars: 2 per row, 3 rows */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <MiniLineChart title="Pronunciation" points={pillarsWindow.pronunciation} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={150} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Fluency" points={pillarsWindow.fluency} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={150} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Grammar" points={pillarsWindow.grammar} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={150} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Expressions" points={pillarsWindow.expressions} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={150} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Vocabulary" points={pillarsWindow.vocabulary} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={150} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Comprehension" points={pillarsWindow.comprehension} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={150} autoY={false} axisMode="labels" axisOpacity={0.08} />
      </section>

      {!loading && sessions.length === 0 && (
        <div className="text-sm text-gray-600 dark:text-gray-300">No data yet. Start practicing to see your progress here.</div>
      )}
    </div>
  );
}
