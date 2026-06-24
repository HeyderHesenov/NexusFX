"use client";

import { useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "lucide-react";
import type { Asset, AssetType } from "@/types";
import { useI18n } from "@/lib/i18n";
import { useClickOutside } from "@/lib/useClickOutside";

type Filter = "all" | AssetType;

// "Hamısı" + tam tip sırası — heç bir kateqoriya düşmür.
const FILTERS: Filter[] = [
  "all",
  "crypto",
  "stock",
  "index",
  "forex",
  "metal",
  "commodity",
  "industrial",
];

/**
 * Tək-seçim aktiv seçici — trigger seçilmiş aktivi göstərir. Açılan paneldə
 * istifadəçi kateqoriya çipini özü seçir (məs. "Forex" → yalnız forex cütləri) +
 * yanında axtarış. Siqnal (alert) formu üçün. Seçimdə bağlanır.
 */
export function AssetSelect({
  assets,
  value,
  onChange,
}: {
  assets: Asset[];
  value: string;
  onChange: (key: string) => void;
}) {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => setOpen(false));

  const selectedLabel = assets.find((a) => a.key === value)?.label ?? value;

  // Yalnız registry-də həqiqətən mövcud olan tiplərin çipini göstər.
  const present = useMemo(() => new Set(assets.map((a) => a.type)), [assets]);
  const chips = FILTERS.filter((f) => f === "all" || present.has(f as AssetType));

  const query = q.trim().toLowerCase();
  const view = useMemo(
    () =>
      assets.filter(
        (a) =>
          (filter === "all" || a.type === filter) &&
          (!query ||
            a.label.toLowerCase().includes(query) ||
            a.key.toLowerCase().includes(query)),
      ),
    [assets, filter, query],
  );

  function openPanel() {
    // Kontekst: seçilmiş aktivin kateqoriyasında aç.
    const selType = assets.find((a) => a.key === value)?.type;
    setFilter(selType ?? "all");
    setQ("");
    setOpen(true);
  }

  function pick(key: string) {
    onChange(key);
    setOpen(false);
    setQ("");
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => (open ? setOpen(false) : openPanel())}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex min-w-40 items-center justify-between gap-2 rounded-lg border border-border bg-bg px-3 py-2 text-sm transition-colors hover:border-accent/60 focus:border-accent focus:outline-none"
      >
        <span className="font-medium">{selectedLabel}</span>
        <ChevronDown
          size={15}
          className={`shrink-0 text-muted transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="absolute z-30 mt-2 w-72 rounded-xl border border-border bg-surface shadow-2xl fade-up">
          {/* kateqoriya çipləri + axtarış */}
          <div className="border-b border-border p-2">
            <div className="flex flex-wrap gap-1">
              {chips.map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setFilter(f)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                    filter === f
                      ? "bg-accent text-black"
                      : "text-muted hover:text-text"
                  }`}
                >
                  {f === "all" ? t("sub.all") : t(`atype.${f}`)}
                </button>
              ))}
            </div>
            <div className="relative mt-2">
              <Search
                size={15}
                className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted"
              />
              <input
                autoFocus
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder={t("picker.search")}
                className="w-full rounded-lg border border-border bg-bg py-2 pl-8 pr-2 text-sm text-text placeholder:text-muted/70 focus:border-accent focus:outline-none"
              />
            </div>
          </div>

          {/* nəticə siyahısı */}
          <div className="max-h-60 overflow-y-auto py-1">
            {view.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted">
                {t("picker.none")}
              </p>
            ) : (
              view.map((a) => {
                const on = a.key === value;
                return (
                  <button
                    key={a.key}
                    type="button"
                    onClick={() => pick(a.key)}
                    className={`flex w-full items-center justify-between px-4 py-2 text-sm transition-colors hover:bg-surface-hover ${
                      on ? "text-accent" : "text-text"
                    }`}
                  >
                    <span className="font-medium">{a.label}</span>
                    {on && <Check size={15} className="shrink-0" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
