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

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        // 1) Fetch sessions (all pages)
        const res = await getAllUserSessions();
        if (!mounted) return;
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
        if (!mounted) return;
        const map: Record<string, FeedbackSummaryResponse> = {};
        for (const p of pairs) if (p) map[p[0]] = p[1];
        setSummaries(map);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || "Failed to load progress");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
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

  // Default visible window: last 14 days including today (local time)
  const [xStart, xEnd] = lastNDaysDomain(14);
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
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Progress</h1>
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
          heightPx={240}
          autoY={false}
          yPadding={0}
          minYRange={0.02}
          axisMode="labels"
          axisOpacity={0.05}
        />
      </section>

      {/* Pillars: 2 per row, 3 rows */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <MiniLineChart title="Pronunciation" points={pillarsWindow.pronunciation} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={140} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Fluency" points={pillarsWindow.fluency} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={140} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Grammar" points={pillarsWindow.grammar} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={140} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Expressions" points={pillarsWindow.expressions} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={140} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Vocabulary" points={pillarsWindow.vocabulary} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={140} autoY={false} axisMode="labels" axisOpacity={0.08} />
        <MiniLineChart title="Comprehension" points={pillarsWindow.comprehension} yDomain={[0, 10]} xDomain={[xStart, xEnd]} className="text-gray-700 dark:text-gray-300" heightPx={140} autoY={false} axisMode="labels" axisOpacity={0.08} />
      </section>

      {!loading && sessions.length === 0 && (
        <div className="text-sm text-gray-600 dark:text-gray-300">No data yet. Start practicing to see your progress here.</div>
      )}
    </div>
  );
}
