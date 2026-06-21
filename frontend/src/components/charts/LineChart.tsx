"use client";

export interface LineSeries {
  label: string;
  color: string;
  points: { date: string; value: number }[];
}

export const SERIES_COLORS = [
  "#ff7a1a",
  "#3b82f6",
  "#22c55e",
  "#a855f7",
  "#ef4444",
];

/**
 * Universal SVG xətt qrafiki (bir və ya bir neçə seriya).
 * normalize=true → hər seriya başlanğıcdan 100-ə nisbətdə (müqayisə üçün).
 */
export function LineChart({
  series,
  height = 260,
  normalize = false,
}: {
  series: LineSeries[];
  height?: number;
  normalize?: boolean;
}) {
  const W = 760;
  const H = height;
  const PAD = { top: 16, right: 16, bottom: 28, left: 52 };

  const norm = series
    .filter((s) => s.points.length >= 2)
    .map((s) => {
      const base = s.points[0].value || 1;
      return {
        ...s,
        vals: s.points.map((p) =>
          normalize ? (p.value / base) * 100 : p.value,
        ),
      };
    });

  if (norm.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-muted">
        —
      </div>
    );
  }

  const len = Math.max(...norm.map((s) => s.vals.length));
  const allY = norm.flatMap((s) => s.vals);
  const minY = Math.min(...allY);
  const maxY = Math.max(...allY);
  const spanY = maxY - minY || 1;

  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const sx = (i: number) => PAD.left + (i / (len - 1)) * innerW;
  const sy = (v: number) => PAD.top + innerH - ((v - minY) / spanY) * innerH;

  const ticks = Array.from({ length: 4 }, (_, i) => minY + (spanY * i) / 3);
  const dates = norm[0].points.map((p) => p.date);
  const first = dates[0];
  const last = dates[dates.length - 1];

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img">
        {ticks.map((tv, i) => (
          <g key={i}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={sy(tv)}
              y2={sy(tv)}
              stroke="currentColor"
              className="text-border"
              strokeWidth={1}
            />
            <text
              x={PAD.left - 6}
              y={sy(tv) + 3}
              textAnchor="end"
              className="fill-muted font-mono text-[9px]"
            >
              {normalize ? tv.toFixed(0) : tv.toLocaleString()}
            </text>
          </g>
        ))}

        <text x={PAD.left} y={H - 8} className="fill-muted font-mono text-[9px]">
          {first}
        </text>
        <text
          x={W - PAD.right}
          y={H - 8}
          textAnchor="end"
          className="fill-muted font-mono text-[9px]"
        >
          {last}
        </text>

        {norm.map((s, si) => (
          <path
            key={si}
            d={s.vals
              .map((v, i) => `${i === 0 ? "M" : "L"}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`)
              .join(" ")}
            fill="none"
            stroke={s.color}
            strokeWidth={2}
          />
        ))}
      </svg>

      {series.length > 1 && (
        <div className="mt-2 flex flex-wrap items-center justify-center gap-4 text-xs">
          {norm.map((s, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <span
                className="h-2 w-3 rounded-sm"
                style={{ background: s.color }}
              />
              {s.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
