import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Tailwind siniflərini təhlükəsiz birləşdirir. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

import type { NewsItem } from "@/types";

/** Cari dilə uyğun başlıq + mətn seçir; tərcümə yoxdursa orijinala düşür. */
export function localizedNews(
  news: NewsItem,
  lang: string,
): { title: string; body: string } {
  const tr = news.translations?.[lang];
  // Hər sahə müstəqil: tərcümə varsa onu, yoxdursa orijinala düş.
  return {
    title: tr?.title || news.title,
    body: tr?.body || news.summary || "",
  };
}

/** ISO tarixi "DD.MM.YYYY · HH:MM" formatına salır. */
export function formatDateTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()} · ${p(
    d.getHours(),
  )}:${p(d.getMinutes())}`;
}
