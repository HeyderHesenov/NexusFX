"use client";

import { useMemo, useState } from "react";
import { Check, Plus, Search } from "lucide-react";
import type { Asset } from "@/types";
import { useI18n } from "@/lib/i18n";

const TYPE_ORDER = ["index", "forex", "metal", "commodity", "crypto"] as const;

/**
 * Axtarışlı aktiv seçici — İzləmə və Müqayisə üçün paylaşılır.
 * Yazıldıqda düz filtr; boşdursa tipə görə qruplaşma.
 */
export function AssetPicker({
  assets,
  isSelected,
  onToggle,
  disableUnselected = false,
}: {
  assets: Asset[];
  isSelected: (key: string) => boolean;
  onToggle: (key: string) => void;
  disableUnselected?: boolean;
}) {
  const { t } = useI18n();
  const [q, setQ] = useState("");

  const query = q.trim().toLowerCase();
  const filtered = useMemo(
    () =>
      query
        ? assets.filter(
            (a) =>
              a.label.toLowerCase().includes(query) ||
              a.key.toLowerCase().includes(query),
          )
        : assets,
    [assets, query],
  );

  const groups = useMemo(() => {
    const by: Record<string, Asset[]> = {};
    for (const a of filtered) (by[a.type] ??= []).push(a);
    return TYPE_ORDER.filter((tp) => by[tp]?.length).map((tp) => ({
      type: tp,
      items: by[tp],
    }));
  }, [filtered]);

  function Tile({ a }: { a: Asset }) {
    const on = isSelected(a.key);
    const dim = disableUnselected && !on;
    return (
      <button
        onClick={() => !dim && onToggle(a.key)}
        disabled={dim}
        className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm transition-all duration-150 ${
          on
            ? "border-accent bg-accent/12 text-accent"
            : dim
              ? "cursor-not-allowed border-border bg-surface text-muted/40"
              : "border-border bg-surface text-text hover:border-accent/50 hover:bg-surface-hover"
        }`}
      >
        <span className="truncate font-medium">{a.label}</span>
        {on ? <Check size={15} className="shrink-0" /> : <Plus size={15} className="shrink-0 text-muted" />}
      </button>
    );
  }

  return (
    <div className="rounded-card border border-border bg-surface/40 p-4">
      {/* axtarış */}
      <div className="relative mb-4">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
        />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("picker.search")}
          className="w-full rounded-lg border border-border bg-bg py-2.5 pl-9 pr-3 text-sm text-text placeholder:text-muted/70 focus:border-accent focus:outline-none"
        />
      </div>

      <div className="max-h-80 space-y-4 overflow-y-auto pr-1">
        {groups.length === 0 && (
          <p className="py-8 text-center text-sm text-muted">{t("picker.none")}</p>
        )}
        {groups.map((g) => (
          <div key={g.type}>
            <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted">
              {t(`atype.${g.type}`)} · {g.items.length}
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {g.items.map((a) => (
                <Tile key={a.key} a={a} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
