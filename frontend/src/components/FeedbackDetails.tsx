"use client";

import React from "react";
import type { FeedbackResponse, PillarFeedback } from "@/lib/api";

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
    <div className="rounded-xl bg-black/5 dark:bg-white/5 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="inline-flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-gray-500/60 dark:bg-gray-300/60" />
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{label}</div>
        </div>
        {data?.score != null && (
          <div className="text-xs font-mono px-2 py-1 rounded-full border border-black/10 dark:border-white/10 text-gray-700 dark:text-gray-200">
            {data.score}
          </div>
        )}
      </div>
      {data?.summary && (
        <div className="text-sm text-gray-800 dark:text-gray-200">{data.summary}</div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ListBlock title="Errors" items={data?.errors} />
        <ListBlock title="Suggestions" items={data?.suggestions} />
      </div>
    </div>
  );
}

export default function FeedbackDetails({ feedback }: { feedback: FeedbackResponse }) {
  const dt = feedback.created_at ? new Date(feedback.created_at) : null;
  const dateFmt = dt ? dt.toLocaleString() : "";

  return (
    <div className="space-y-6">
      {/* Overall */}
      <div className="flex items-center justify-between gap-3">
        <SectionPill label="Feedback" />
        <div className="flex items-center gap-3 text-[11px] md:text-xs text-gray-500 dark:text-gray-400">
          {dateFmt && <span>{dateFmt}</span>}
          <span>•</span>
          <span className="font-mono">{feedback.generated_by}</span>
          <span>•</span>
          <span className="font-mono">{feedback.session_id}</span>
        </div>
      </div>

      {feedback.overall_score != null && (
        <div className="text-sm text-gray-700 dark:text-gray-300">
          Overall score: <span className="font-medium text-gray-900 dark:text-gray-100">{feedback.overall_score}</span>
        </div>
      )}

      {/* General summary and assessment */}
      {(feedback.general_summary || feedback.general_feedback) && (
        <div className="rounded-xl bg-black/5 dark:bg-white/5 p-4 space-y-3">
          {feedback.general_summary && (
            <InfoRow label="Summary" value={<span className="whitespace-pre-wrap">{feedback.general_summary}</span>} />
          )}
          {feedback.general_feedback && (
            <InfoRow label="Assessment" value={<span className="whitespace-pre-wrap">{feedback.general_feedback}</span>} />
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <ListBlock title="General errors" items={feedback.general_errors} />
            <ListBlock title="General suggestions" items={feedback.general_suggestions} />
          </div>
        </div>
      )}

      {/* Pillars */}
      <div className="space-y-3">
        <SectionPill label="Pillars" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
