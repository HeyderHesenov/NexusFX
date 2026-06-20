/**
 * Tab üzrə təqvim kateqoriyaları — MarketCalendar dropdown-u bunları göstərir.
 * Hər kateqoriya: göstərmə növü (kind) + məlumatı çəkən load().
 */
import {
  getCalendar,
  getCryptoCalendar,
  getEarnings,
  getMajorsCalendar,
  getMetals,
} from "@/lib/api";
import type { Category } from "@/types";

export type CalKind =
  | "earnings"
  | "events"
  | "unlocks"
  | "prices"
  | "cryptoEvents";

export interface CalCategory {
  key: string;
  labelKey: string;
  kind: CalKind;
  load: () => Promise<unknown[]>;
}

const US: CalCategory[] = [
  { key: "earnings", labelKey: "market.earnings", kind: "earnings", load: getEarnings },
  {
    key: "ai",
    labelKey: "market.aiStocks",
    kind: "earnings",
    load: () => getEarnings().then((d) => d.filter((e) => e.ai)),
  },
  {
    key: "usd",
    labelKey: "market.usdEvents",
    kind: "events",
    load: () => getCalendar().then((d) => d.filter((e) => e.country === "USD")),
  },
];

const FOREX: CalCategory[] = [
  { key: "currencies", labelKey: "market.currencies", kind: "events", load: getCalendar },
  { key: "metals", labelKey: "market.metals", kind: "prices", load: getMetals },
];

const CRYPTO: CalCategory[] = [
  {
    key: "major",
    labelKey: "market.majors",
    kind: "cryptoEvents",
    load: getMajorsCalendar,
  },
  {
    key: "rwa",
    labelKey: "market.rwa",
    kind: "unlocks",
    load: () => getCryptoCalendar().then((d) => d.filter((u) => u.sector === "rwa")),
  },
  {
    key: "ai",
    labelKey: "market.aiCoins",
    kind: "unlocks",
    load: () => getCryptoCalendar().then((d) => d.filter((u) => u.sector === "ai")),
  },
];

export const CATEGORIES: Record<Category, CalCategory[]> = {
  us: US,
  forex: FOREX,
  crypto: CRYPTO,
};
