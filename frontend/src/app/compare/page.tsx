"use client";

import { useEffect, useState } from "react";
import { GitCompare } from "lucide-react";
import { AppNav } from "@/components/layout/AppNav";
import { LineChart, SERIES_COLORS } from "@/components/charts/LineChart";
import { getAssets, getAssetDetail } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Asset, AssetDetail } from "@/types";

const RANGES = ["1mo", "3mo", "6mo", "1y"];
const MAX = 5;

export default function ComparePage() {
  const { t } = useI18n();
  const [registry, setRegistry] = useState<Asset[]>([]);
  const [selected, setSelected] = useState<string[]>(["btc", "spx"]);
  const [range, setRange] = useState("3mo");
  const [details, setDetails] = useState<Record<string, AssetDetail>>({});

  useEffect(() => {
    getAssets().then(setRegistry);
  }, []);

  useEffect(() => {
    let stop = false;
    Promise.all(selected.map((k) => getAssetDetail(k, range))).then((res) => {
      if (stop) return;
      const map: Record<string, AssetDetail> = {};
      selected.forEach((k, i) => {
        const d = res[i];
        if (d) map[k] = d;
      });
      setDetails(map);
    });
    return () => {
      stop = true;
    };
  }, [selected, range]);

  function toggle(key: string) {
    setSelected((cur) =>
      cur.includes(key)
        ? cur.filter((k) => k !== key)
        : cur.length < MAX
          ? [...cur, key]
          : cur,
    );
  }

  const series = selected
    .map((k, i) => {
      const h = details[k]?.history;
      if (!h || h.points.length < 2) return null;
      return {
        label: h.label,
        color: SERIES_COLORS[i % SERIES_COLORS.length],
        points: h.points.map((p) => ({ date: p.date, value: p.close })),
      };
    })
    .filter(Boolean) as { label: string; color: string; points: { date: string; value: number }[] }[];

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-7xl px-5 py-8">
        <div className="mb-2 flex items-center gap-2">
          <GitCompare size={18} className="text-accent" />
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("nav.compare")}
          </h1>
        </div>
        <p className="mb-5 text-sm text-muted">{t("compare.subtitle")}</p>

        {/* aktiv seçimi */}
        <div className="mb-4 flex flex-wrap gap-2">
          {registry.map((a) => {
            const on = selected.includes(a.key);
            return (
              <button
                key={a.key}
                onClick={() => toggle(a.key)}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-all ${
                  on
                    ? "border-accent bg-accent/15 text-accent"
                    : "border-border bg-surface text-muted hover:text-text"
                }`}
              >
                {a.label}
              </button>
            );
          })}
        </div>

        {/* dövr */}
        <div className="mb-5 flex gap-1 rounded-xl border border-border bg-surface p-1 w-fit">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`rounded-lg px-3 py-1 text-sm font-medium transition-all ${
                range === r ? "bg-accent text-black" : "text-muted hover:text-text"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* normallaşdırılmış qrafik */}
        <section className="rounded-card border border-border bg-surface p-5">
          <p className="mb-3 font-mono text-[10px] uppercase tracking-wider text-muted">
            {t("compare.normalized")}
          </p>
          <LineChart series={series} normalize height={300} />
        </section>

        {/* cədvəl */}
        <section className="mt-5 overflow-hidden rounded-card border border-border">
          <table className="w-full text-sm">
            <thead className="bg-surface text-muted">
              <tr>
                <th className="px-4 py-2 text-left font-medium">{t("compare.asset")}</th>
                <th className="px-4 py-2 text-right font-medium">{t("compare.price")}</th>
                <th className="px-4 py-2 text-right font-medium">{t("compare.rangeChg")}</th>
              </tr>
            </thead>
            <tbody>
              {selected.map((k) => {
                const d = details[k];
                const q = d?.quote;
                const h = d?.history;
                const chg = h?.changePct ?? 0;
                return (
                  <tr key={k} className="border-t border-border">
                    <td className="px-4 py-2.5 font-medium">{q?.label ?? k}</td>
                    <td className="px-4 py-2.5 text-right font-mono">
                      {q?.val ?? "—"}
                    </td>
                    <td
                      className={`px-4 py-2.5 text-right font-mono ${chg >= 0 ? "text-up" : "text-down"}`}
                    >
                      {chg >= 0 ? "+" : ""}
                      {chg.toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}
