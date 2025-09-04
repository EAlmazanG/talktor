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
  xDomain?: [Date, Date]; // optional fixed time domain; if provided it is used for scaling and ticks
  className?: string; // set text color to affect stroke (uses currentColor)
  heightPx?: number; // visual height; default 140
  showAxes?: boolean; // draw axes and tick labels; default false
  showGrid?: boolean; // draw faint gridlines; default false
  pointRadius?: number; // point radius; default 3
  strokeWidth?: number; // line thickness; default 2
  autoY?: boolean; // auto fit Y domain to data within [0,10]; default true
  yPadding?: number; // extra padding ratio for autoY (e.g., 0.15 adds 15% margins)
  axisMode?: "none" | "lines" | "labels" | "full"; // controls axis rendering; default derived from showAxes
  axisOpacity?: number; // opacity for axis lines; default 0.12
  axisLabelWeightClass?: string; // override font weight for axis labels, e.g., 'font-thin'
  axisLabelOpacity?: number; // opacity for axis label text; default 0.42
  axisLabelSizeClass?: string; // tailwind size classes for axis labels; default 'text-[7px] md:text-[9px]'
  minYRange?: number; // enforce a minimum Y range to avoid a flattened look; default 0.5
  paddingOverrides?: Partial<{ left: number; right: number; top: number; bottom: number }>; // customize internal paddings
}

// Utility: clamp a value to [min, max]
function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

export default function MiniLineChart({
  title,
  points,
  yDomain = [0, 10],
  xDomain,
  className,
  heightPx = 140,
  showAxes = false,
  showGrid = false,
  pointRadius = 1.75,
  strokeWidth = 1.25,
  autoY = true,
  yPadding = 0.15,
  axisMode,
  axisOpacity = 0.12,
  axisLabelWeightClass,
  axisLabelOpacity = 0.42,
  axisLabelSizeClass,
  minYRange = 0.5,
  paddingOverrides,
}: MiniLineChartProps) {
  // Fixed viewBox to make the SVG scalable; CSS height controls visual size
  const vb = { w: 600, h: 200 };
  const effAxisMode = axisMode ?? (showAxes ? "full" : "none");
  const hasLabels = effAxisMode === "full" || effAxisMode === "labels";
  // Generous and balanced padding on all sides to avoid clipping and achieve visual centering
  const basePad = { left: hasLabels ? 52 : 14, right: hasLabels ? 52 : 12, top: 16, bottom: hasLabels ? 44 : 12 };
  const pad = { ...basePad, ...(paddingOverrides || {}) };
  const labelWeight = axisLabelWeightClass ?? "font-extralight";
  const labelSize = axisLabelSizeClass ?? "text-[7px] md:text-[9px]";

  const sorted = useMemo(() => {
    const arr = (points || []).filter((p) => Number.isFinite(p.value) && p.date instanceof Date);
    arr.sort((a, b) => a.date.getTime() - b.date.getTime());
    return arr;
  }, [points]);

  const domain = useMemo(() => {
    if (xDomain && xDomain[0] instanceof Date && xDomain[1] instanceof Date) {
      const minT = xDomain[0].getTime();
      const maxT = xDomain[1].getTime();
      return { minT, maxT: Math.max(maxT, minT + 1) };
    }
    if (sorted.length === 0) return { minT: 0, maxT: 1 };
    const minT = sorted[0].date.getTime();
    const maxT = sorted[sorted.length - 1].date.getTime();
    return { minT, maxT: Math.max(maxT, minT + 1) };
  }, [sorted, xDomain?.[0], xDomain?.[1]]);

  const GLOBAL_MIN = 0;
  const GLOBAL_MAX = 10;
  let yMin = yDomain[0];
  let yMax = yDomain[1];
  if (autoY && sorted.length > 0) {
    let dataMin = Number.POSITIVE_INFINITY;
    let dataMax = Number.NEGATIVE_INFINITY;
    for (const p of sorted) {
      if (Number.isFinite(p.value)) {
        dataMin = Math.min(dataMin, p.value);
        dataMax = Math.max(dataMax, p.value);
      }
    }
    if (!Number.isFinite(dataMin) || !Number.isFinite(dataMax)) {
      dataMin = GLOBAL_MIN;
      dataMax = GLOBAL_MAX;
    }
    let range = dataMax - dataMin;
    if (range === 0) {
      // Expand a bit around a flat line
      yMin = Math.max(GLOBAL_MIN, dataMin - 1);
      yMax = Math.min(GLOBAL_MAX, dataMax + 1);
    } else {
      const padAmt = range * yPadding;
      yMin = Math.max(GLOBAL_MIN, dataMin - padAmt);
      yMax = Math.min(GLOBAL_MAX, dataMax + padAmt);
      if (yMax - yMin < minYRange) {
        // Ensure a minimum range for visual clarity
        const mid = (yMax + yMin) / 2;
        yMin = Math.max(GLOBAL_MIN, mid - minYRange / 2);
        yMax = Math.min(GLOBAL_MAX, mid + minYRange / 2);
      }
    }
    if (yMax <= yMin) {
      yMax = Math.min(GLOBAL_MAX, yMin + minYRange);
    }
  }

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
  }, [sorted, yMin, yMax]);

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
    // Use the provided xDomain if available; otherwise derive from data
    let start: Date;
    let end: Date;
    if (xDomain && xDomain[0] instanceof Date && xDomain[1] instanceof Date) {
      start = dayStart(xDomain[0]);
      end = dayStart(xDomain[1]);
    } else {
      if (sorted.length === 0) return [] as Array<{ t: number; x: number; label: string }>;
      start = dayStart(sorted[0].date);
      end = dayStart(sorted[sorted.length - 1].date);
    }
    const oneDay = 24 * 60 * 60 * 1000;
    const totalDays = Math.max(1, Math.round((end.getTime() - start.getTime()) / oneDay) + 1);
    const maxTicks = 5;
    const stepDays = Math.max(1, Math.ceil(totalDays / maxTicks));
    const ticksRaw: Array<{ t: number; x: number; label: string }> = [];
    for (let i = 0; i < totalDays; i += stepDays) {
      const t = start.getTime() + i * oneDay;
      if (t > end.getTime()) break;
      const dt = new Date(t);
      const label = `${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
      ticksRaw.push({ t, x: scaleX(t), label });
    }
    // Ensure the end day label is included
    const endT = end.getTime();
    const endLabel = `${String(end.getMonth() + 1).padStart(2, "0")}-${String(end.getDate()).padStart(2, "0")}`;
    const endTick = { t: endT, x: scaleX(endT), label: endLabel };
    if (!ticksRaw.some((tk) => tk.t === endT)) ticksRaw.push(endTick);

    // Sort and de-duplicate by time
    ticksRaw.sort((a, b) => a.t - b.t);
    const uniq: Array<{ t: number; x: number; label: string }> = [];
    const seen = new Set<number>();
    for (const tk of ticksRaw) {
      if (seen.has(tk.t)) continue;
      seen.add(tk.t);
      uniq.push(tk);
    }

    // Enforce a minimum gap (in viewBox units) between labels to avoid overlap; always keep the last one
    const minGap = 48; // ~8% of viewBox width (scales with container width)
    const spaced: Array<{ t: number; x: number; label: string }> = [];
    for (let i = 0; i < uniq.length; i++) {
      const tk = uniq[i];
      if (spaced.length === 0) {
        spaced.push(tk);
      } else if (tk.x - spaced[spaced.length - 1].x >= minGap) {
        spaced.push(tk);
      } else if (i === uniq.length - 1) {
        // Replace the previous with the end tick if too close, so the final day is visible
        spaced[spaced.length - 1] = tk;
      }
    }
    return spaced;
  }, [sorted, domain.minT, domain.maxT, xDomain?.[0], xDomain?.[1]]);

  // Hover state for tooltip
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const hoverPoint = hoverIndex != null && sorted[hoverIndex] ? sorted[hoverIndex] : null;

  return (
    <div className={`rounded-lg border border-black/10 dark:border-white/10 p-4 ${className || ""}`}>
      {title && (
        <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-4 md:mb-5 font-semibold">
          {title}
        </div>
      )}
      <div className="w-full" style={{ height: heightPx }}>
        <svg viewBox={`0 0 ${vb.w} ${vb.h}`} preserveAspectRatio="none" className="w-full h-full">
          {/* Axes lines (only for 'lines' and 'full') */}
          {(effAxisMode === "lines" || effAxisMode === "full") && (
            <g className="stroke-current" opacity={axisOpacity}>
              {/* Y axis line */}
              <line x1={pad.left} x2={pad.left} y1={pad.top} y2={vb.h - pad.bottom} vectorEffect="non-scaling-stroke" />
              {/* X axis line */}
              <line x1={pad.left} x2={vb.w - pad.right} y1={vb.h - pad.bottom} y2={vb.h - pad.bottom} vectorEffect="non-scaling-stroke" />
            </g>
          )}

          {/* Y axis tick labels (10 to 0). For 'labels', render only text; for 'full', render ticks and optional gridlines too. */}
          {(effAxisMode === "full" || effAxisMode === "labels") && (
            <g className="text-xs fill-current stroke-current">
              {yTicks.map((t, idx) => (
                <g key={`y-${idx}`}>
                  {effAxisMode === "full" && (
                    <line x1={pad.left - 4} x2={pad.left} y1={t.y} y2={t.y} className="stroke-current" opacity={0.6} vectorEffect="non-scaling-stroke" />
                  )}
                  <text x={pad.left - 6} y={t.y} textAnchor="end" dominantBaseline="middle" className={`fill-current ${labelWeight} ${labelSize} tabular-nums`} opacity={axisLabelOpacity}>
                    {t.v}
                  </text>
                  {/* Light gridline */}
                  {effAxisMode === "full" && showGrid && (
                    <line x1={pad.left} x2={vb.w - pad.right} y1={t.y} y2={t.y} className="stroke-current" opacity={0.06} vectorEffect="non-scaling-stroke" />
                  )}
                </g>
              ))}
            </g>
          )}

          {/* X axis tick labels (days). For 'labels', render only text; for 'full', include tick marks. */}
          {(effAxisMode === "full" || effAxisMode === "labels") && (
            <g className="text-xs fill-current stroke-current">
              {xTicks.map((t, idx) => (
                <g key={`x-${idx}`}>
                  {effAxisMode === "full" && (
                    <line x1={t.x} x2={t.x} y1={vb.h - pad.bottom} y2={vb.h - pad.bottom + 4} className="stroke-current" opacity={0.6} vectorEffect="non-scaling-stroke" />
                  )}
                  <text
                    x={t.x}
                    y={vb.h - pad.bottom + 18}
                    textAnchor={idx === 0 ? "start" : idx === xTicks.length - 1 ? "end" : "middle"}
                    className={`fill-current ${labelWeight} ${labelSize} tabular-nums`}
                    opacity={axisLabelOpacity}
                    dx={idx === 0 ? 4 : idx === xTicks.length - 1 ? -4 : 0}
                  >
                    {t.label}
                  </text>
                </g>
              ))}
            </g>
          )}

          {/* Chart path */}
          {sorted.length > 1 && (
            <path d={pathD} className="fill-none stroke-current" strokeWidth={strokeWidth} opacity={0.85} vectorEffect="non-scaling-stroke" />
          )}

          {/* Draw point markers */}
          {sorted.map((p, i) => (
            <circle
              key={`pt-${i}`}
              cx={scaleX(p.date.getTime())}
              cy={scaleY(p.value)}
              r={pointRadius}
              className="fill-current"
              opacity={0.85}
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
                    vectorEffect="non-scaling-stroke"
                  />
                  {/* Highlight dot */}
                  <circle
                    cx={scaleX(hoverPoint.date.getTime())}
                    cy={scaleY(hoverPoint.value)}
                    r={Math.max(5, pointRadius + 2)}
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
