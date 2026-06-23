"use client";

import { useState } from "react";
import { History, Search } from "lucide-react";
import { AppNav } from "@/components/layout/AppNav";
import { Footer } from "@/components/layout/Footer";
import { AnalogPanel } from "@/components/news/HistoricalAnalogs";
import { searchAnalogs } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { AnalogResult } from "@/types";

// Nümunə ssenarilər — qısa, dil-müstəqil (embedding + alias-lar tutur).
const EXAMPLES = ["Fed raises rates", "High CPI inflation", "BTC ETF inflows", "Oil supply cut"];

export default function AnalogsPage() {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const [data, setData] = useState<AnalogResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function run(query: string) {
    const text = query.trim();
    if (!text) return;
    setQ(text);
    setSearched(true);
    setLoading(true);
    setData(null);
    const res = await searchAnalogs(text);
    setData(res);
    setLoading(false);
  }

  return (
    <div className="flex min-h-screen flex-col">
      <AppNav />
      <main className="mx-auto w-full max-w-3xl px-5 py-8">
        <div className="mb-1.5 flex items-center gap-2">
          <History size={18} className="text-accent" />
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("analog.pageTitle")}
          </h1>
        </div>
        <p className="mb-5 text-sm text-muted">{t("analog.pageSubtitle")}</p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            run(q);
          }}
          className="flex gap-2"
        >
          <div className="relative flex-1">
            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("analog.searchPlaceholder")}
              className="w-full rounded-xl border border-border bg-surface py-2.5 pl-9 pr-3 text-sm outline-none transition-colors focus:border-accent/50"
            />
          </div>
          <button
            type="submit"
            className="rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-black transition-opacity hover:brightness-110 disabled:opacity-50"
            disabled={!q.trim()}
          >
            {t("analog.search")}
          </button>
        </form>

        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => run(ex)}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted transition-colors hover:border-accent/40 hover:text-text"
            >
              {ex}
            </button>
          ))}
        </div>

        {searched && <AnalogPanel data={data} loading={loading} />}
      </main>
      <Footer />
    </div>
  );
}
