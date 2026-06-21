"use client";

import { useEffect } from "react";
import { getAssetQuote } from "@/lib/api";
import { markTriggered, readAlerts } from "@/lib/alerts";

const POLL_MS = 45_000;

/** Fonda qiymət siqnallarını yoxlayır; həddi keçəndə bildiriş göndərir.
    UI yox — bütün səhifələrdə (layout-da) işləyir. */
export function AlertWatcher() {
  useEffect(() => {
    let stopped = false;

    async function check() {
      const active = readAlerts().filter((a) => a.triggeredAt === null);
      if (active.length === 0) return;
      const keys = [...new Set(active.map((a) => a.key))];
      const quotes = await Promise.all(keys.map((k) => getAssetQuote(k)));
      const priceByKey: Record<string, number> = {};
      keys.forEach((k, i) => {
        const q = quotes[i];
        if (q) priceByKey[k] = q.price;
      });

      for (const a of active) {
        const price = priceByKey[a.key];
        if (price === undefined) continue;
        const hit =
          a.direction === "above" ? price >= a.price : price <= a.price;
        if (!hit) continue;
        fire(a.label, a.direction, a.price, price);
        markTriggered(a.id);
      }
    }

    function fire(
      label: string,
      dir: "above" | "below",
      target: number,
      price: number,
    ) {
      const arrow = dir === "above" ? "▲" : "▼";
      const body = `${label} ${arrow} ${target} (indi ${price})`;
      try {
        if (
          typeof Notification !== "undefined" &&
          Notification.permission === "granted"
        ) {
          new Notification("NexusIQ — qiymət siqnalı", { body });
        }
      } catch {
        /* səssiz */
      }
      window.dispatchEvent(
        new CustomEvent("nexusiq:alert-fired", { detail: { label, body } }),
      );
    }

    const id = window.setInterval(() => {
      if (!stopped) void check();
    }, POLL_MS);
    void check();

    return () => {
      stopped = true;
      window.clearInterval(id);
    };
  }, []);

  return null;
}
