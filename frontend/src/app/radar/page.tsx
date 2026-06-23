"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Radar, Sparkles, Zap } from "lucide-react";
import { AppNav } from "@/components/layout/AppNav";
import { Footer } from "@/components/layout/Footer";
import { Sparkline } from "@/components/charts/Sparkline";
import { getRadar, getRadarExplain } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { RadarBreakdown, RadarCategory, RadarItem } from "@/types";

const TABS: { key: RadarCategory; labelKey: string }[] = [
  { key: "crypto", labelKey: "radar.tab.crypto" },
  { key: "stock", labelKey: "radar.tab.stock" },
  { key: "commodity", labelKey: "radar.tab.commodity" },
  { key: "forex", labelKey: "radar.tab.forex" },
];

// Bal səviyyəsinə görə rəng — yüksək=accent, orta=amber, aşağı=muted.
function tierColor(score: number): string {
  if (score >= 70) return "var(--accent)";
  if (score >= 45) return "#fbbf24";
  return "var(--muted)";
}

/** Signature — fürsət balı radial halqası (0..100). */
function ScoreRing({ score }: { score: number }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(100, score)) / 100);
  const color = tierColor(score);
  return (
    <div className="relative h-[68px] w-[68px] shrink-0">
      <svg width="68" height="68" viewBox="0 0 68 68" className="-rotate-90">
        <circle
          cx="34"
          cy="34"
          r={r}
          fill="none"
          stroke="var(--border)"
          strokeWidth="5"
        />
        <circle
          cx="34"
          cy="34"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={off}
          style={{ transition: "stroke-dashoffset 600ms ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className="font-mono text-lg font-semibold tabular-nums"
          style={{ color }}
        >
          {Math.round(score)}
        </span>
      </div>
    </div>
  );
}

/** Bal komponentləri — dörd nazik zolaq (momentum/sentiment/təsir/anomaliya). */
function ScoreBars({ b }: { b: RadarBreakdown }) {
  const { t } = useI18n();
  const rows: { key: keyof RadarBreakdown; labelKey: string }[] = [
    { key: "momentum", labelKey: "radar.bd.momentum" },
    { key: "sentiment", labelKey: "radar.bd.sentiment" },
    { key: "impact", labelKey: "radar.bd.impact" },
    { key: "anomaly", labelKey: "radar.bd.anomaly" },
  ];
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
      {rows.map(({ key, labelKey }) => {
        const v = b[key];
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="w-16 shrink-0 text-[10px] uppercase tracking-wide text-muted">
              {t(labelKey)}
            </span>
            <span className="h-1 flex-1 overflow-hidden rounded-full bg-border">
              <span
                className="block h-full rounded-full"
                style={{ width: `${v}%`, background: tierColor(v) }}
              />
            </span>
            <span className="w-6 text-right font-mono text-[10px] tabular-nums text-muted">
              {Math.round(v)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function RadarCard({ item, rank }: { item: RadarItem; rank: number }) {
  const { t, lang } = useI18n();
  const [explain, setExplain] = useState<string | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [asked, setAsked] = useState(false);

  const onExplain = useCallback(async () => {
    setExplaining(true);
    setAsked(true);
    const text = await getRadarExplain(item.key, lang);
    setExplain(text);
    setExplaining(false);
  }, [item.key, lang]);

  return (
    <div className="rounded-card border border-border bg-surface transition-colors hover:bg-surface-hover">
      <div className="grid grid-cols-[auto_1fr_auto] items-center gap-4 p-4 sm:gap-5 sm:p-5">
        {/* sıra + bal halqası */}
        <div className="flex items-center gap-3 sm:gap-4">
          <span className="w-5 text-center font-mono text-sm text-muted tabular-nums">
            {rank}
          </span>
          <ScoreRing score={item.score} />
        </div>

        {/* aktiv + komponentlər */}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Link
              href={`/asset/${item.key}`}
              className="truncate font-semibold hover:text-accent"
            >
              {item.label}
            </Link>
            <span className="text-[11px] uppercase tracking-wide text-muted">
              {item.type}
            </span>
            {item.anomaly && (
              <span className="inline-flex items-center gap-1 rounded-full border border-down/40 px-1.5 py-0.5 text-[10px] font-medium text-down">
                <Zap size={10} />
                {item.anomaly}
              </span>
            )}
          </div>
          <div className="mt-2.5 max-w-md">
            <ScoreBars b={item.breakdown} />
          </div>
        </div>

        {/* qiymət + trend */}
        <div className="flex flex-col items-end gap-1.5">
          <div className="font-mono text-sm font-semibold tabular-nums">
            {item.val}
          </div>
          <div
            className={`font-mono text-xs tabular-nums ${
              item.up ? "text-up" : "text-down"
            }`}
          >
            {item.chg}
          </div>
          <div className="mt-0.5 hidden sm:block">
            <Sparkline values={item.spark} width={96} height={28} />
          </div>
        </div>
      </div>

      {/* xəbərlər + AI izah */}
      <div className="border-t border-border px-4 py-3 sm:px-5">
        {item.news.length > 0 && (
          <ul className="mb-2 space-y-1.5">
              {item.news.map((n) => (
                <li key={n.id} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent" />
                  <Link
                    href={`/news/${n.id}`}
                    className="line-clamp-1 text-muted transition-colors hover:text-text"
                  >
                    {(lang === "az" && n.titleAz) || n.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}

          {asked ? (
            <p className="flex items-start gap-2 text-sm text-text">
              <Sparkles size={14} className="mt-0.5 shrink-0 text-accent" />
              <span>
                {explaining
                  ? t("radar.explaining")
                  : explain || t("radar.noExplain")}
              </span>
            </p>
          ) : (
            <button
              onClick={onExplain}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-accent transition-opacity hover:opacity-80"
            >
              <Sparkles size={13} />
              {t("radar.explain")}
            </button>
          )}
        </div>
    </div>
  );
}

export default function RadarPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<RadarCategory>("crypto");
  const [rows, setRows] = useState<RadarItem[]>([]);
  const [status, setStatus] = useState<"loading" | "ready">("loading");

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    getRadar(tab).then((data) => {
      if (cancelled) return;
      setRows(data);
      setStatus("ready");
    });
    return () => {
      cancelled = true;
    };
  }, [tab]);

  return (
    <div className="flex min-h-screen flex-col">
      <AppNav />
      <main className="mx-auto w-full max-w-4xl px-5 py-8">
        {/* başlıq */}
        <div className="mb-5">
          <div className="mb-1.5 flex items-center gap-2">
            <Radar size={18} className="text-accent" />
            <h1 className="text-2xl font-semibold tracking-tight">
              {t("radar.title")}
            </h1>
          </div>
          <p className="text-sm text-muted">{t("radar.subtitle")}</p>
        </div>

        {/* kateqoriya tabları */}
        <div className="mb-5 flex gap-1 rounded-xl border border-border bg-surface p-1">
          {TABS.map((tb) => (
            <button
              key={tb.key}
              onClick={() => setTab(tb.key)}
              className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                tab === tb.key
                  ? "bg-accent text-black"
                  : "text-muted hover:text-text"
              }`}
            >
              {t(tb.labelKey)}
            </button>
          ))}
        </div>

        {/* skeleton */}
        {status === "loading" && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-32 animate-pulse rounded-card border border-border bg-surface"
              />
            ))}
          </div>
        )}

        {/* boş */}
        {status === "ready" && rows.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-card border border-border bg-surface py-20 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-border">
              <Radar size={22} className="text-muted" />
            </div>
            <p className="text-sm text-muted">{t("radar.empty")}</p>
          </div>
        )}

        {/* siyahı */}
        {status === "ready" && rows.length > 0 && (
          <div className="space-y-3">
            {rows.map((item, i) => (
              <RadarCard key={item.key} item={item} rank={i + 1} />
            ))}
            <p className="pt-2 text-center text-[11px] text-muted">
              {t("radar.footnote")}
            </p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
