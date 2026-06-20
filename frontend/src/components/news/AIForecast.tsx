"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus, Activity, LineChart } from "lucide-react";
import { getForecast } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Forecast, Impact } from "@/types";

const STYLE: Record<Impact, { cls: string; Icon: typeof TrendingUp }> = {
  up: { cls: "text-emerald-400", Icon: TrendingUp },
  down: { cls: "text-rose-400", Icon: TrendingDown },
  mixed: { cls: "text-amber-400", Icon: Activity },
  neutral: { cls: "text-muted", Icon: Minus },
};

export function AIForecast({ id }: { id: string }) {
  const { t, lang } = useI18n();
  const [fc, setFc] = useState<Forecast | null>(null);

  useEffect(() => {
    let alive = true;
    setFc(null);
    getForecast(id, lang).then((d) => alive && setFc(d));
    return () => {
      alive = false;
    };
  }, [id, lang]);

  const pairs = fc?.pairs ?? [];

  return (
    <section className="mt-8">
      <div className="mb-3 flex items-center gap-2">
        <LineChart size={16} className="text-accent" />
        <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-accent">
          {t("news.forecast")}
        </h2>
      </div>

      {/* yüklənir */}
      {!fc && (
        <div className="space-y-2.5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-12 animate-pulse rounded-xl border border-border bg-surface"
            />
          ))}
          <p className="pt-1 text-xs text-muted">{t("news.forecastLoading")}</p>
        </div>
      )}

      {fc && !fc.ready && (
        <p className="rounded-lg border border-border bg-surface px-3.5 py-2.5 text-xs text-muted">
          {t("news.forecastNone")}
        </p>
      )}

      {fc?.ready && (
        <>
          {fc.summary && (
            <p className="mb-4 text-[15px] leading-relaxed text-text/90">
              {fc.summary}
            </p>
          )}

          <ul className="space-y-2.5">
            {pairs.map((p, i) => {
              const { cls, Icon } = STYLE[p.impact] ?? STYLE.neutral;
              return (
                <li
                  key={`${p.sym}-${i}`}
                  className="flex items-start gap-3 rounded-xl border border-border bg-surface px-4 py-3"
                >
                  <span className="mt-0.5 flex w-20 shrink-0 items-center gap-1.5 font-mono text-sm font-semibold">
                    <Icon size={15} className={cls} />
                    {p.sym}
                  </span>
                  <span className="text-[14px] leading-snug text-text/80">
                    {p.reason}
                  </span>
                </li>
              );
            })}
          </ul>

          <p className="mt-3 text-[11px] text-muted/70">{t("news.forecastNote")}</p>
        </>
      )}
    </section>
  );
}
