"use client";

import { Star } from "lucide-react";
import { toggleWatch, useWatched } from "@/lib/watchlist";
import { useI18n } from "@/lib/i18n";

/** Aktivi izləmə siyahısına əlavə/çıxar. */
export function WatchButton({ assetKey }: { assetKey: string }) {
  const on = useWatched(assetKey);
  const { t } = useI18n();
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleWatch(assetKey);
      }}
      title={on ? t("watch.remove") : t("watch.add")}
      aria-label={on ? t("watch.remove") : t("watch.add")}
      className={`grid h-9 w-9 place-items-center rounded-lg border transition-all duration-200 ${
        on
          ? "border-accent/60 bg-accent/15 text-accent"
          : "border-border bg-surface text-muted hover:border-accent/40 hover:text-text"
      }`}
    >
      <Star size={16} fill={on ? "currentColor" : "none"} />
    </button>
  );
}
