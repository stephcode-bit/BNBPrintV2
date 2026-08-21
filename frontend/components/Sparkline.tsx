"use client";

import { useMemo } from "react";

/**
 * Lightweight inline-SVG sparkline for a series of numbers. No charting
 * library needed for this — it's fed by session-accumulated snapshots (see
 * TokenChart.tsx), not historical OHLC data, since the backend doesn't
 * persist time-series history yet (see README for a note on adding a
 * `/api/tokens/{address}/history` endpoint + candles table if you want
 * full historical charts).
 */
export default function Sparkline({
  values,
  width = 320,
  height = 64,
  color = "#F0B90B",
}: {
  values: number[];
  width?: number;
  height?: number;
  color?: string;
}) {
  const path = useMemo(() => {
    if (values.length < 2) return "";
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const step = width / (values.length - 1);
    return values
      .map((v, i) => {
        const x = i * step;
        const y = height - ((v - min) / range) * (height - 8) - 4;
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [values, width, height]);

  if (values.length < 2) {
    return (
      <div className="flex items-center justify-center text-xs text-bnb-muted" style={{ width, height }}>
        Collecting live data…
      </div>
    );
  }

  const last = values[values.length - 1];
  const first = values[0];
  const trendColor = last >= first ? "#0ECB81" : "#F6465D";

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <defs>
        <linearGradient id="sparkline-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={trendColor} stopOpacity="0.25" />
          <stop offset="100%" stopColor={trendColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L${width},${height} L0,${height} Z`} fill="url(#sparkline-fill)" />
      <path d={path} fill="none" stroke={trendColor} strokeWidth={1.75} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
