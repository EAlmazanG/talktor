"use client";

// Minimal, dependency-free line chart using SVG.
// All code and comments must be in English

import React, { useMemo, useState } from "react";

export type ChartPoint = {
  date: Date;
  value: number;
};

export interface MiniLineChartProps {
  title?: string;
  points: ChartPoint[];
  yDomain?: [number, number]; // default [0, 10]
  className?: string; // set text color to affect stroke (uses currentColor)
  heightPx?: number; // visual height; default 140
}

// Utility: clamp a value to [min, max]
function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

export default function MiniLineChart({
  title,
  points,
  yDomain = [0, 10],
  className,
  heightPx = 140,
}: MiniLineChartProps) {
  // Fixed viewBox to make the SVG scalable; CSS height controls visual size
  const vb = { w: 600, h: 200 };
  const pad = { left: 46, right: 10, top: 10, bottom: 36 };

  const sorted = useMemo(() => {
    const arr = (points || []).filter((p) => Number.isFinite(p.value) && p.date instanceof Date);
    arr.sort((a, b) => a.date.getTime() - b.date.getTime());
    return arr;
  }, [points]);

  const domain = useMemo(() => {
    if (sorted.length === 0) return { minT: 0, maxT: 1 };
    const minT = sorted[0].date.getTime();
    const maxT = sorted[sorted.length - 1].date.getTime();
    return { minT, maxT: Math.max(maxT, minT + 1) };
  }, [sorted]);

  const yMin = yDomain[0];
  const yMax = yDomain[1];

  const scaleX = (t: number) => {
    const dx = domain.maxT - domain.minT;
    const frac = (t - domain.minT) / dx;
    return pad.left + frac * (vb.w - pad.left - pad.right);
  };
  const scaleY = (v: number) => {
    const vv = clamp(v, yMin, yMax);
    const frac = (vv - yMin) / (yMax - yMin);
    return vb.h - pad.bottom - frac * (vb.h - pad.top - pad.bottom);
  };

  const pathD = useMemo(() => {
    if (sorted.length === 0) return "";
    let d = "";
    sorted.forEach((p, i) => {
      const x = scaleX(p.date.getTime());
      const y = scaleY(p.value);
      d += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });
    return d;
  }, [sorted]);

  // Y ticks (labels from 10 down to 0 by 2 by default)
  const yTicks = useMemo(() => {
    const step = 2;
    const ticks: number[] = [];
    for (let v = yMax; v >= yMin; v -= step) ticks.push(Number(v.toFixed(0)));
    return ticks.map((v) => ({ v, y: scaleY(v) }));
  }, [yMin, yMax]);

  // X ticks (days). Show up to ~7 labels across the domain.
  function dayStart(d: Date) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }
  const xTicks = useMemo(() => {
    if (sorted.length === 0) return [] as Array<{ t: number; x: number; label: string }>;
    const start = dayStart(sorted[0].date);
    const end = dayStart(sorted[sorted.length - 1].date);
    const oneDay = 24 * 60 * 60 * 1000;
    const totalDays = Math.max(1, Math.round((end.getTime() - start.getTime()) / oneDay) + 1);
    const maxTicks = 7;
    const stepDays = Math.max(1, Math.ceil(totalDays / maxTicks));
    const ticks: Array<{ t: number; x: number; label: string }> = [];
    for (let i = 0; i < totalDays; i += stepDays) {
      const t = start.getTime() + i * oneDay;
      const dt = new Date(t);
      const label = `${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
      ticks.push({ t, x: scaleX(t), label });
    }
    // Always include the end day label
    if (ticks.length === 0 || ticks[ticks.length - 1].t !== end.getTime()) {
      ticks.push({ t: end.getTime(), x: scaleX(end.getTime()), label: `${String(end.getMonth() + 1).padStart(2, "0")}-${String(end.getDate()).padStart(2, "0")}` });
    }
    return ticks;
  }, [sorted, domain.minT, domain.maxT]);

  // Hover state for tooltip
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const hoverPoint = hoverIndex != null && sorted[hoverIndex] ? sorted[hoverIndex] : null;

  return (
    <div className={`rounded-lg border border-black/10 dark:border-white/10 p-3 ${className || ""}`}>
      {title && (
        <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
          {title}
        </div>
      )}
      <div className="w-full" style={{ height: heightPx }}>
        <svg viewBox={`0 0 ${vb.w} ${vb.h}`} preserveAspectRatio="none" className="w-full h-full">
          {/* Axes */}
          <g className="stroke-current" opacity={0.6}>
            {/* Y axis line */}
            <line x1={pad.left} x2={pad.left} y1={pad.top} y2={vb.h - pad.bottom} />
            {/* X axis line */}
            <line x1={pad.left} x2={vb.w - pad.right} y1={vb.h - pad.bottom} y2={vb.h - pad.bottom} />
          </g>

          {/* Y axis ticks and labels (10 to 0) */}
          <g className="text-xs fill-current stroke-current">
            {yTicks.map((t, idx) => (
              <g key={`y-${idx}`}>
                <line x1={pad.left - 4} x2={pad.left} y1={t.y} y2={t.y} className="stroke-current" opacity={0.6} />
                <text x={pad.left - 6} y={t.y} textAnchor="end" dominantBaseline="middle" className="fill-current text-[10px] md:text-[11px] tabular-nums" opacity={0.8}>
                  {t.v}
                </text>
                {/* Light gridline */}
                <line x1={pad.left} x2={vb.w - pad.right} y1={t.y} y2={t.y} className="stroke-current" opacity={0.06} />
              </g>
            ))}
          </g>

          {/* X axis ticks and labels (days) */}
          <g className="text-xs fill-current stroke-current">
            {xTicks.map((t, idx) => (
              <g key={`x-${idx}`}> 
                <line x1={t.x} x2={t.x} y1={vb.h - pad.bottom} y2={vb.h - pad.bottom + 4} className="stroke-current" opacity={0.6} />
                <text x={t.x} y={vb.h - pad.bottom + 14} textAnchor="middle" className="fill-current text-[10px] md:text-[11px] tabular-nums" opacity={0.8}>
                  {t.label}
                </text>
              </g>
            ))}
          </g>

          {/* Chart path */}
          {sorted.length > 1 && (
            <path d={pathD} className="fill-none stroke-current" strokeWidth={2} />
          )}

          {/* Draw point markers */}
          {sorted.map((p, i) => (
            <circle
              key={`pt-${i}`}
              cx={scaleX(p.date.getTime())}
              cy={scaleY(p.value)}
              r={3}
              className="fill-current"
            >
              <title>{`${p.value.toFixed(1)} on ${String(p.date.getMonth() + 1).padStart(2, "0")}-${String(p.date.getDate()).padStart(2, "0")}`}</title>
            </circle>
          ))}

          {/* Hover overlay */}
          {sorted.length > 0 && (
            <g>
              {/* Transparent overlay to capture pointer */}
              <rect
                x={pad.left}
                y={pad.top}
                width={vb.w - pad.left - pad.right}
                height={vb.h - pad.top - pad.bottom}
                fill="transparent"
                onMouseMove={(e) => {
                  const bbox = (e.currentTarget as SVGRectElement).getBoundingClientRect();
                  const relX = e.clientX - bbox.left;
                  const xInViewBox = (relX / bbox.width) * (vb.w - pad.left - pad.right) + pad.left;
                  // find nearest point by X
                  let bestIdx = 0;
                  let bestDist = Number.POSITIVE_INFINITY;
                  for (let i = 0; i < sorted.length; i++) {
                    const px = scaleX(sorted[i].date.getTime());
                    const d = Math.abs(px - xInViewBox);
                    if (d < bestDist) {
                      bestDist = d;
                      bestIdx = i;
                    }
                  }
                  setHoverIndex(bestIdx);
                }}
                onMouseLeave={() => setHoverIndex(null)}
              />

              {hoverPoint && (
                <g pointerEvents="none">
                  {/* Guideline */}
                  <line
                    x1={scaleX(hoverPoint.date.getTime())}
                    x2={scaleX(hoverPoint.date.getTime())}
                    y1={pad.top}
                    y2={vb.h - pad.bottom}
                    className="stroke-current"
                    opacity={0.2}
                  />
                  {/* Highlight dot */}
                  <circle
                    cx={scaleX(hoverPoint.date.getTime())}
                    cy={scaleY(hoverPoint.value)}
                    r={5}
                    className="fill-current"
                    opacity={0.9}
                  />
                  {/* Tooltip box */}
                  {(() => {
                    const x = scaleX(hoverPoint.date.getTime());
                    const y = scaleY(hoverPoint.value);
                    const boxW = 110;
                    const boxH = 36;
                    const padBox = 8;
                    let bx = x + 8;
                    let by = y - boxH - 6;
                    // keep inside bounds
                    if (bx + boxW > vb.w - pad.right) bx = x - boxW - 8;
                    if (bx < pad.left) bx = pad.left + 2;
                    if (by < pad.top) by = y + 8;
                    const dateLabel = `${String(hoverPoint.date.getMonth() + 1).padStart(2, "0")}-${String(hoverPoint.date.getDate()).padStart(2, "0")}`;
                    return (
                      <g>
                        <rect x={bx} y={by} width={boxW} height={boxH} rx={6} className="fill-current" opacity={0.08} />
                        <rect x={bx} y={by} width={boxW} height={boxH} rx={6} className="stroke-current fill-transparent" opacity={0.2} />
                        <text x={bx + padBox} y={by + 16} className="fill-current text-[11px] tabular-nums">
                          {hoverPoint.value.toFixed(1)} / 10
                        </text>
                        <text x={bx + padBox} y={by + 28} className="fill-current text-[11px] tabular-nums" opacity={0.8}>
                          {dateLabel}
                        </text>
                      </g>
                    );
                  })()}
                </g>
              )}
            </g>
          )}
        </svg>
      </div>
    </div>
  );
}
