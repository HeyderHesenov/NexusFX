import { AppNav } from "@/components/layout/AppNav";
import { Footer } from "@/components/layout/Footer";

/**
 * Route keçidi zamanı görünən skelet (App Router loading.tsx fallback-ı).
 *
 * Niyə: səhifələr klik-mount client komponentləridir. loading.tsx olmadan
 * Next yeni route hazır olana qədər köhnə səhifəni saxlayır — donma hissi.
 * Bu skelet klik anında dərhal görünür: nav yerində qalır, başlıq altında
 * skan zolağı axır, kontent yeri shimmer bloklarla tutulur.
 */
export function RouteSkeleton() {
  return (
    <div className="flex min-h-screen flex-col">
      <AppNav />

      {/* üst skan zolağı — "feed yüklənir" siqnalı */}
      <div className="relative h-0.5 overflow-hidden bg-border/40">
        <span className="route-scan absolute top-0 h-full w-[35%] rounded-full bg-accent" />
      </div>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8">
        {/* eyebrow + başlıq */}
        <div className="skeleton h-3 w-28 rounded" />
        <div className="skeleton mt-4 h-9 w-2/3 max-w-md rounded-lg" />
        <div className="skeleton mt-3 h-3.5 w-1/2 max-w-sm rounded" />

        {/* kontent şəbəkəsi */}
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-card border border-border bg-surface p-4"
            >
              <div className="skeleton h-32 w-full rounded-lg" />
              <div className="skeleton mt-4 h-3.5 w-3/4 rounded" />
              <div className="skeleton mt-2.5 h-3 w-1/2 rounded" />
            </div>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
}
