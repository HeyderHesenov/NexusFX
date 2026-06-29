import type { Config } from "tailwindcss";

/**
 * Rəng sistemi — Black / Orange / White (ilkin).
 * Sonra asanlıqla dəyişmək üçün CSS dəyişənlərinə bağlıdır (globals.css).
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-hover": "var(--surface-hover)",
        border: "var(--border)",
        accent: "var(--accent)",
        "accent-soft": "var(--accent-soft)",
        text: "var(--text)",
        muted: "var(--muted)",
        up: "var(--up)",
        down: "var(--down)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "14px",
      },
      maxWidth: {
        // Terminal məzmun eni — geniş monitorda ekranı doldurur, ultra-genişdə
        // sətirlər oxunaqlı qalsın deyə sərhəd. Nav/Footer/data səhifələri paylaşır.
        app: "1760px",
      },
    },
  },
  plugins: [],
};

export default config;
