import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // BNB Chain / Binance brand palette
        bnb: {
          yellow: "#F0B90B",
          gold: "#FCD535",
          black: "#0B0E11",
          dark: "#181A20",
          panel: "#1E2329",
          border: "#2B3139",
          muted: "#848E9C",
          green: "#0ECB81",
          red: "#F6465D",
        },
      },
      fontFamily: {
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono-face)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(240, 185, 11, 0.25)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(240,185,11,0.45)" },
          "70%": { boxShadow: "0 0 0 8px rgba(240,185,11,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(240,185,11,0)" },
        },
        "slide-in": {
          "0%": { transform: "translateY(-8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slide-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};
export default config;
