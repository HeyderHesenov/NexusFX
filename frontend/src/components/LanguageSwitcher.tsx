"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { useI18n, LANGS } from "@/lib/i18n";

/** Dil seçici — qlobus düyməsi + açılan siyahı. */
export function LanguageSwitcher() {
  const { lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Kənara klikləyəndə bağla.
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const current = LANGS.find((l) => l.code === lang)!;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        title={current.label}
        aria-label={current.label}
        className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-muted transition-colors duration-200 hover:bg-surface-hover hover:text-text"
      >
        <span className="text-base leading-none">{current.flag}</span>
        <ChevronDown
          size={13}
          className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-44 overflow-hidden rounded-xl border border-border bg-surface shadow-2xl fade-up">
          {LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => {
                setLang(l.code);
                setOpen(false);
              }}
              className={`flex w-full items-center justify-between px-3.5 py-2.5 text-sm transition-colors duration-150 hover:bg-surface-hover ${
                l.code === lang ? "text-accent" : "text-text"
              }`}
            >
              <span className="flex items-center gap-2.5">
                <span>{l.flag}</span>
                {l.label}
              </span>
              {l.code === lang && <Check size={15} />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
