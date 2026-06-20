"use client";

import { useEffect, useState } from "react";
import { Gauge } from "lucide-react";
import { getFearGreed } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { FearGreed as FG } from "@/types";

/** 0-100 dəyər üçün rəng zonası. */
function tone(v: number): string {
  if (v < 25) return "#f43f5e"; // rose — extreme fear
  if (v < 45) return "#fb923c"; // orange — fear
  if (v < 55) return "#facc15"; // yellow — neutral
  if (v < 75) return "#a3e635"; // lime — greed
  return "#34d399"; // emerald — extreme greed
}

export function FearGreed() {
  const { t } = useI18n();
  const [fg, setFg] = useState<FG | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let alive = true;
    getFearGreed().then((d) => {
      if (!alive) return;
      setFg(d);
      setDone(true);
    });
    return () => {
      alive = false;
    };
  }, []);

  if (done && !fg) return null; // səssiz keç — dizayn pozulmasın

  const v = fg?.value ?? 0;
  const color = tone(v);

  return (
    <section className="mb-6 flex items-center gap-5 rounded-card border border-border bg-surface px-5 py-4">
      {/* dairəvi gauge */}
      <div className="relative h-16 w-16 shrink-0">
        <svg viewBox="0 0 36 36" className="h-16 w-16 -rotate-90">
          <circle
            cx="18"
            cy="18"
            r="15.9155"
            fill="none"
            stroke="var(--border, #232a3a)"
            strokeWidth="3"
          />
          <circle
            cx="18"
            cy="18"
            r="15.9155"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${fg ? v : 0} 100`}
            className="transition-all duration-700"
          />
        </svg>
        <span
          className="absolute inset-0 flex items-center justify-center text-lg font-bold tabular-nums"
          style={{ color }}
        >
          {fg ? v : "—"}
        </span>
      </div>

      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <Gauge size={14} className="text-accent" />
          <span className="font-mono text-xs uppercase tracking-[0.15em] text-accent">
            {t("market.feargreed")}
          </span>
        </div>
        <p className="mt-1 text-base font-semibold" style={{ color }}>
          {fg?.label ?? "—"}
        </p>
      </div>
    </section>
  );
}
