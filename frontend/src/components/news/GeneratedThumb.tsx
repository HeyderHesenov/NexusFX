"use client";

import { Bitcoin, DollarSign, TrendingUp, Fuel } from "lucide-react";
import type { Category } from "@/types";

/**
 * Brendli örtük şəkli — şəkli olmayan xəbərlər üçün. Heç bir qiymət xətti YOX;
 * təmiz qradiyent + solğun kateqoriya motivi + wordmark. Forma id-dən
 * deterministik çıxır (eyni xəbər → eyni örtük).
 */
const CFG: Record<Category, { hue: number; Icon: typeof Bitcoin; label: string }> = {
  forex: { hue: 205, Icon: DollarSign, label: "FOREX" },
  us: { hue: 150, Icon: TrendingUp, label: "US MARKETS" },
  crypto: { hue: 32, Icon: Bitcoin, label: "CRYPTO" },
  commodities: { hue: 95, Icon: Fuel, label: "COMMODITIES" },
};

function hashStr(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function GeneratedThumb({
  seed,
  category,
  className,
}: {
  seed: string;
  category: Category;
  className?: string;
}) {
  const cfg = CFG[category];
  const s = hashStr(seed);
  const hue = cfg.hue + ((s % 22) - 11);
  const angle = 120 + (s % 60);
  const color = `hsl(${hue} 80% 58%)`;
  const Icon = cfg.Icon;

  return (
    <div
      className={`relative overflow-hidden ${className ?? ""}`}
      style={{
        background: `linear-gradient(${angle}deg, hsl(${hue} 42% 16%), hsl(${hue} 50% 9%) 70%, #0a0a0b)`,
      }}
      aria-hidden
    >
      {/* yumşaq işıq ləkəsi */}
      <div
        className="absolute -right-10 -top-12 h-44 w-44 rounded-full blur-2xl"
        style={{ background: color, opacity: 0.22 }}
      />

      {/* solğun nöqtə toxuması */}
      <div
        className="absolute inset-0 opacity-[0.14]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,.7) 1px, transparent 1px)",
          backgroundSize: "16px 16px",
        }}
      />

      {/* böyük solğun kateqoriya ikonu */}
      <Icon
        size={120}
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.16]"
        style={{ color }}
        strokeWidth={1.5}
      />

      {/* kateqoriya etiketi */}
      <span
        className="absolute left-3.5 top-3 font-mono text-[10px] font-semibold tracking-[0.18em]"
        style={{ color }}
      >
        {cfg.label}
      </span>

      {/* wordmark */}
      <span className="absolute bottom-2.5 left-3.5 font-mono text-[10px] font-semibold tracking-wider text-white/80">
        Nexus<span style={{ color }}>IQ</span>
      </span>
    </div>
  );
}
