"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Star } from "lucide-react";
import { AppNav } from "@/components/layout/AppNav";
import { WatchButton } from "@/components/assets/WatchButton";
import { AssetPicker } from "@/components/assets/AssetPicker";
import { getAssets, getAssetQuote } from "@/lib/api";
import { toggleWatch, useWatchlist } from "@/lib/watchlist";
import { useI18n } from "@/lib/i18n";
import type { Asset, AssetQuote } from "@/types";

export default function WatchlistPage() {
  const { t } = useI18n();
  const watched = useWatchlist();
  const [registry, setRegistry] = useState<Asset[]>([]);
  const [quotes, setQuotes] = useState<Record<string, AssetQuote>>({});

  useEffect(() => {
    getAssets().then(setRegistry);
  }, []);

  useEffect(() => {
    if (watched.length === 0) return;
    let stop = false;
    async function load() {
      const qs = await Promise.all(watched.map((k) => getAssetQuote(k)));
      if (stop) return;
      const map: Record<string, AssetQuote> = {};
      watched.forEach((k, i) => {
        const q = qs[i];
        if (q) map[k] = q;
      });
      setQuotes(map);
    }
    load();
    const id = window.setInterval(load, 60_000);
    return () => {
      stop = true;
      window.clearInterval(id);
    };
  }, [watched]);


  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-7xl px-5 py-8">
        <div className="mb-6 flex items-center gap-2">
          <Star size={18} className="text-accent" />
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("nav.watchlist")}
          </h1>
        </div>

        {watched.length === 0 ? (
          <p className="rounded-card border border-dashed border-border py-16 text-center text-sm text-muted">
            {t("watch.empty")}
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {watched.map((k) => {
              const q = quotes[k];
              return (
                <div
                  key={k}
                  className="flex items-center justify-between gap-3 rounded-card border border-border bg-surface p-4"
                >
                  <Link href={`/asset/${k}`} className="min-w-0 flex-1">
                    <p className="truncate font-semibold">
                      {q?.label ?? k.toUpperCase()}
                    </p>
                    {q ? (
                      <div className="mt-1 flex items-baseline gap-2">
                        <span className="font-mono text-sm">{q.val}</span>
                        <span
                          className={`font-mono text-xs ${q.up ? "text-up" : "text-down"}`}
                        >
                          {q.chg}
                        </span>
                      </div>
                    ) : (
                      <div className="mt-2 h-3 w-20 animate-pulse rounded bg-surface-hover" />
                    )}
                  </Link>
                  <WatchButton assetKey={k} />
                </div>
              );
            })}
          </div>
        )}

        {/* aktiv idarəetmə — axtarışlı seçici */}
        {registry.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-3 text-sm font-semibold">{t("watch.addTitle")}</h2>
            <AssetPicker
              assets={registry}
              isSelected={(k) => watched.includes(k)}
              onToggle={toggleWatch}
            />
          </section>
        )}
      </main>
    </div>
  );
}
