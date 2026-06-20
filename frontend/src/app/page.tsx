"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { Ticker } from "@/components/market/Ticker";
import { AIAssistantFab } from "@/components/ai/AIAssistantFab";
import { NewsCard } from "@/components/news/NewsCard";
import { FearGreed } from "@/components/market/FearGreed";
import { MarketCalendar } from "@/components/market/MarketCalendar";
import { CATEGORIES } from "@/lib/marketCategories";
import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Category, NewsItem } from "@/types";

const TITLES: Record<Category, string> = {
  forex: "Forex",
  us: "US Markets",
  crypto: "Crypto",
};

export default function HomePage() {
  const { t } = useI18n();
  const [active, setActive] = useState<Category>("forex");
  const [items, setItems] = useState<NewsItem[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  const load = useCallback(async (cat: Category) => {
    setStatus("loading");
    try {
      const data = await apiGet<NewsItem[]>(`/news?category=${cat}&limit=30`);
      setItems(data);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    load(active);
  }, [active, load]);

  function logout() {
    localStorage.removeItem("nexusiq_session");
    location.reload();
  }

  return (
    <div className="min-h-screen">
      <Header active={active} onChange={setActive} onLogout={logout} />
      <Ticker />

      <main className="mx-auto max-w-7xl px-5 py-8">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent">
              {TITLES[active]}
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">
              {t("home.marketNews")}
            </h1>
          </div>
          {status === "ready" && (
            <span className="font-mono text-xs text-muted">
              {items.length} {t("home.count")}
            </span>
          )}
        </div>

        <MarketCalendar key={active} categories={CATEGORIES[active]} />
        {active === "crypto" && <FearGreed />}

        {status === "loading" && (
          <NewsGrid>
            {Array.from({ length: 9 }).map((_, i) => (
              <NewsCardSkeleton key={i} />
            ))}
          </NewsGrid>
        )}

        {status === "error" && (
          <EmptyState
            title={t("home.error")}
            hint={t("home.errorHint")}
            onRetry={() => load(active)}
            retryLabel={t("home.retry")}
          />
        )}

        {status === "ready" && items.length === 0 && (
          <EmptyState title={t("home.empty")} hint={t("home.emptyHint")} />
        )}

        {status === "ready" && items.length > 0 && (
          <NewsGrid>
            {items.map((n) => (
              <NewsCard key={n.id} news={n} />
            ))}
          </NewsGrid>
        )}
      </main>

      <AIAssistantFab />
    </div>
  );
}

function NewsGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {children}
    </div>
  );
}

function EmptyState({
  title,
  hint,
  onRetry,
  retryLabel,
}: {
  title: string;
  hint?: string;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-border py-20 text-center">
      <p className="text-base font-medium text-text">{title}</p>
      {hint && <p className="mt-1.5 max-w-sm text-sm text-muted">{hint}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 rounded-lg border border-border bg-surface px-4 py-2 text-sm text-text transition-colors hover:border-accent hover:text-accent"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
}

/** Xəbər kartının yüklənmə skeleti (shimmer). */
function NewsCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-card border border-border bg-surface">
      <div className="aspect-[16/9] animate-pulse bg-surface-hover" />
      <div className="space-y-3 p-4">
        <div className="h-4 w-full animate-pulse rounded bg-surface-hover" />
        <div className="h-4 w-4/5 animate-pulse rounded bg-surface-hover" />
        <div className="h-3 w-1/3 animate-pulse rounded bg-surface-hover" />
      </div>
    </div>
  );
}
