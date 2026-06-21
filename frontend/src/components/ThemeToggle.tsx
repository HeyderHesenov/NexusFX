"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";
import { useI18n } from "@/lib/i18n";

/** Açıq/qaranlıq tema keçidi. */
export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const { t } = useI18n();
  const dark = theme === "dark";
  return (
    <button
      onClick={toggle}
      title={dark ? t("theme.light") : t("theme.dark")}
      aria-label={dark ? t("theme.light") : t("theme.dark")}
      className="grid h-9 w-9 place-items-center rounded-lg text-muted transition-colors duration-200 hover:bg-surface-hover hover:text-accent"
    >
      {dark ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}
