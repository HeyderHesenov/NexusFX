"use client";

import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { getNewsAnalogs } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { AnalogResult } from "@/types";

const WINS: ("1" | "5" | "30")[] = ["1", "5", "30"];

function pct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}
function moveCls(v: number | null | undefined): string {
  if (v === null || v === undefined) return "text-muted";
  return v > 0 ? "text-up" : v < 0 ? "text-down" : "text-muted";
}

function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
}

/** Tarixi Analoq paneli — saf təsviri (xəbər səhifəsi + /analogs paylaşır). */
export function AnalogPanel({
  data,
  loading,
}: {
  data: AnalogResult | null;
  loading: boolean;
}) {
  const { t } = useI18n();
  const winLabel = (w: string) => t(`analog.win${w}`);

  return (
    <section className="mt-8">
      <div className="mb-1 flex items-center gap-2">
        <History size={16} className="text-accent" />
        <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-accent">
          {t("analog.title")}
        </h2>
      </div>
      <p className="mb-3 text-sm text-muted">{t("analog.subtitle")}</p>

      {loading && (
        <div className="space-y-2.5">
          <div className="grid grid-cols-3 gap-2">
            {WINS.map((w) => (
              <div
                key={w}
                className="h-16 animate-pulse rounded-xl border border-border bg-surface"
              />
            ))}
          </div>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-12 animate-pulse rounded-xl border border-border bg-surface"
            />
          ))}
          <p className="pt-1 text-xs text-muted">{t("analog.loading")}</p>
        </div>
      )}

      {!loading && (!data?.ready || !data.count) && (
        <p className="rounded-lg border border-border bg-surface px-3.5 py-2.5 text-xs text-muted">
          {t("analog.empty")}
        </p>
      )}

      {!loading && data?.ready && !!data.count && (
        <>
          {/* aşkarlanan aktiv + nümunə sayı */}
          <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="rounded-full border border-accent/40 bg-accent-soft px-2.5 py-0.5 font-mono text-xs font-semibold text-accent">
              {data.asset?.label}
            </span>
            <span className="text-muted">
              {t("analog.basis").replace("{n}", String(data.count))}
            </span>
          </div>

          {/* 3 üfüq — orta hərəkət + hit-rate */}
          <div className="grid grid-cols-3 gap-2">
            {WINS.map((w) => {
              const win = data.windows?.[w];
              return (
                <div
                  key={w}
                  className="rounded-xl border border-border bg-surface px-3 py-2.5"
                >
                  <div className="text-[10px] uppercase tracking-wide text-muted">
                    {winLabel(w)}
                  </div>
                  <div
                    className={`mt-0.5 font-mono text-lg font-semibold tabular-nums ${moveCls(win?.avg)}`}
                  >
                    {pct(win?.avg)}
                  </div>
                  <div className="font-mono text-[10px] text-muted">
                    {win && win.hitRate !== null
                      ? `${Math.round(win.hitRate * 100)}% ${t("analog.hit")}`
                      : "—"}
                  </div>
                </div>
              );
            })}
          </div>

          {/* analoq hadisələr */}
          <ul className="mt-3 space-y-2">
            {data.events?.map((e) => (
              <li
                key={e.id}
                className="flex flex-col gap-2 rounded-xl border border-border bg-surface px-4 py-3 sm:flex-row sm:items-center"
              >
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-[11px] text-muted">
                    {fmtDate(e.publishedAt)}
                  </div>
                  <p className="truncate text-[13px] text-text/80">{e.title}</p>
                </div>
                <div className="grid grid-cols-3 gap-2 sm:w-56 sm:shrink-0">
                  {WINS.map((w) => (
                    <div
                      key={w}
                      className="rounded-lg bg-surface-hover px-2 py-1 text-center"
                    >
                      <div className="text-[9px] uppercase text-muted">
                        {winLabel(w)}
                      </div>
                      <div
                        className={`font-mono text-xs font-semibold tabular-nums ${moveCls(e.moves[w])}`}
                      >
                        {pct(e.moves[w])}
                      </div>
                    </div>
                  ))}
                </div>
              </li>
            ))}
          </ul>

          <p className="mt-3 text-[11px] text-muted/70">{t("analog.note")}</p>
        </>
      )}
    </section>
  );
}

/** Xəbər səhifəsi üçün — saxlanmış embedding ilə analoqları lazy çəkir. */
export function HistoricalAnalogs({ newsId }: { newsId: string }) {
  const { lang } = useI18n();
  const [data, setData] = useState<AnalogResult | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    getNewsAnalogs(newsId, lang).then((d) => alive && setData(d));
    return () => {
      alive = false;
    };
  }, [newsId, lang]);

  return <AnalogPanel data={data} loading={data === null} />;
}
