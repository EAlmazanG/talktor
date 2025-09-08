"use client";

import React, { useMemo } from "react";

export type VoiceDotsProps = {
  level: number; // 0..1 from AI playback
  dots?: number; // number of dots in the row
  className?: string;
};

// Modern dot-style voice waveform visualization.
// - Driven by AI playback level (not microphone input)
// - Uses a cosine window so center dots react more than edges
// - Scales and subtly lifts dots based on the level
export default function VoiceDots({ level, dots = 9, className = "" }: VoiceDotsProps) {
  const clamped = Math.max(0, Math.min(1, level));

  // Precompute positional weights so center dots are larger
  const weights = useMemo(() => {
    const arr: number[] = [];
    const c = (dots - 1) / 2;
    for (let i = 0; i < dots; i++) {
      const x = (i - c) / c; // -1..1
      const w = 0.35 + 0.65 * Math.cos(Math.abs(x) * Math.PI * 0.9); // 0.35..1.0
      arr.push(w);
    }
    return arr;
  }, [dots]);

  return (
    <div className={"flex items-center justify-center " + className}>
      <div className="h-24 md:h-28 flex items-center justify-center">
        <div className="flex items-center justify-center gap-2 md:gap-3">
          {weights.map((w, i) => {
            // Map level to size and slight vertical lift. Keep it subtle for a modern look.
            const amp = clamped * w;
            const size = 10 + amp * 12; // px
            const translateY = -amp * 16; // px upward
            const opacity = 0.5 + amp * 0.5;
            return (
              <div
                key={i}
                className="rounded-full bg-emerald-500 dark:bg-emerald-400 shadow-sm"
                style={{
                  width: size,
                  height: size,
                  transform: `translateY(${translateY}px)`,
                  transition: "transform 80ms linear, width 80ms linear, height 80ms linear, opacity 120ms ease-out",
                  opacity,
                }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
