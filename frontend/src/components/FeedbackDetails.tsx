"use client";

import React from "react";
import type { FeedbackResponse, PillarFeedback } from "@/lib/api";

// Color styles for score-based UI accents
function getScoreStyle(score?: number) {
  if (score == null) {
    return {
      gradient: "from-gray-300 to-gray-500",
      chipBg: "bg-gray-600/10",
      chipBorder: "border-gray-600/20",
      chipText: "text-gray-800 dark:text-gray-100",
    };
  }
  if (score >= 8) {
    return {
      gradient: "from-emerald-400 to-emerald-600",
      chipBg: "bg-emerald-500/10",
      chipBorder: "border-emerald-500/30",
      chipText: "text-emerald-700 dark:text-emerald-200",
    };
  }
  if (score >= 6) {
    return {
      gradient: "from-amber-400 to-amber-600",
      chipBg: "bg-amber-500/10",
      chipBorder: "border-amber-500/30",
      chipText: "text-amber-700 dark:text-amber-200",
    };
  }
  return {
    gradient: "from-rose-400 to-rose-600",
    chipBg: "bg-rose-500/10",
    chipBorder: "border-rose-500/30",
    chipText: "text-rose-700 dark:text-rose-200",
  };
}

function ScoreBadge({ score }: { score?: number }) {
  const s = getScoreStyle(score);
  return (
    <div className={`relative flex items-center justify-center w-24 h-24 md:w-28 md:h-28 rounded-full bg-gradient-to-br ${s.gradient} text-white shadow-md ring-1 ring-white/20`}>
      <div className="text-3xl md:text-4xl font-semibold leading-none tabular-nums">{score != null ? score : "—"}</div>
      <div className="absolute -bottom-2 text-[10px] md:text-xs rounded-full px-2 py-0.5 bg-black/20 backdrop-blur text-white uppercase tracking-wide">
        Score
      </div>
    </div>
  );
}

function MiniScoreBadge({ score }: { score?: number }) {
  const s = getScoreStyle(score);
  return (
    <div className={`flex items-center justify-center w-9 h-9 md:w-10 md:h-10 rounded-full bg-gradient-to-br ${s.gradient} text-white shadow-sm ring-1 ring-white/20`}>
      <div className="text-sm md:text-base font-semibold leading-none tabular-nums">{score != null ? score : "—"}</div>
    </div>
  );
}

function ColoredListBlock({ variant, title, items }: { variant: "errors" | "suggestions"; title: string; items?: string[] }) {
  if (!items || items.length === 0) return null;
  const base =
    variant === "errors"
      ? "bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200"
      : "bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 text-emerald-800 dark:text-emerald-200";
  return (
    <div className={`h-full rounded-lg px-3 py-2 ${base} overflow-auto`}>
      <div className="text-[11px] md:text-xs font-semibold uppercase tracking-wide mb-1">{title}</div>
      <ul className="list-disc pl-5 text-sm leading-relaxed space-y-1.5 marker:text-current break-words text-pretty">
        {items.map((it, idx) => (
          <li key={idx}>{it}</li>
        ))}
      </ul>
    </div>
  );
}

function SectionPill({ label }: { label: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-black/5 dark:bg-white/10 px-2.5 py-1 text-[11px] md:text-xs font-medium uppercase tracking-wide text-gray-700 dark:text-gray-200">
      <span className="h-1.5 w-1.5 rounded-full bg-gray-500/60 dark:bg-gray-300/60" />
      <span>{label}</span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value?: React.ReactNode }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex items-start gap-3 text-sm">
      <div className="w-28 shrink-0 text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-gray-900 dark:text-gray-100">{value}</div>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-1">
      <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{title}</div>
      <ul className="list-disc pl-5 text-sm text-gray-900 dark:text-gray-100 space-y-1">
        {items.map((it, idx) => (
          <li key={idx}>{it}</li>
        ))}
      </ul>
    </div>
  );
}

function PillarCard({ name, data }: { name: string; data: PillarFeedback }) {
  const label = name.charAt(0).toUpperCase() + name.slice(1);
  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex items-center justify-between min-h-[2.5rem]">
        <div className="text-sm uppercase tracking-wide font-semibold text-gray-800 dark:text-gray-100">{label}</div>
        {data?.score != null && <MiniScoreBadge score={data.score} />}
      </div>
      <div className="text-sm leading-relaxed text-gray-800 dark:text-gray-200 break-words text-pretty whitespace-pre-wrap sm:h-24 md:h-28 overflow-auto pr-1">
        {data?.summary}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5 items-stretch sm:h-28 md:h-32">
        <ColoredListBlock variant="errors" title="Errors" items={data?.errors} />
        <ColoredListBlock variant="suggestions" title="Suggestions" items={data?.suggestions} />
      </div>
    </div>
  );
}

export default function FeedbackDetails({ feedback }: { feedback: FeedbackResponse }) {
  const dt = feedback.created_at ? new Date(feedback.created_at) : null;
  const dateFmt = dt ? dt.toLocaleDateString() : "";

  return (
    <div className="space-y-6">
      {/* Overall */}
      <div className="flex items-center justify-between gap-3">
        <SectionPill label="Feedback" />
        {dateFmt && (
          <div className="text-[11px] md:text-xs text-gray-500 dark:text-gray-400">{dateFmt}</div>
        )}
      </div>

      {/* General summary and assessment */}
      {(feedback.general_summary || feedback.general_feedback) && (
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="shrink-0">
              <ScoreBadge score={feedback.overall_score} />
            </div>
            <div className="flex-1 min-w-0 space-y-3">
              {feedback.general_summary && (
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Summary</div>
                  <div className="text-[15px] md:text-base leading-relaxed text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{feedback.general_summary}</div>
                </div>
              )}
              {feedback.general_feedback && (
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Assessment</div>
                  <div className="text-[15px] md:text-base leading-relaxed text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{feedback.general_feedback}</div>
                </div>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <ColoredListBlock variant="errors" title="General errors" items={feedback.general_errors} />
            <ColoredListBlock variant="suggestions" title="General suggestions" items={feedback.general_suggestions} />
          </div>
        </div>
      )}

      {/* Pillars */}
      <div className="space-y-4">
        <SectionPill label="Pillars" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-8 md:gap-y-10 items-stretch">
          <PillarCard name="pronunciation" data={feedback.pronunciation} />
          <PillarCard name="fluency" data={feedback.fluency} />
          <PillarCard name="grammar" data={feedback.grammar} />
          <PillarCard name="expressions" data={feedback.expressions} />
          <PillarCard name="vocabulary" data={feedback.vocabulary} />
          <PillarCard name="comprehension" data={feedback.comprehension} />
        </div>
      </div>
    </div>
  );
}
