/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Capacity tier colours — keep in sync with generate_czml.py
        "fiber-ultra":   "#00E6FF",
        "fiber-high":    "#32C850",
        "fiber-medium":  "#FFC800",
        "fiber-low":     "#FF7800",
        "fiber-unknown": "#8C8C8C",
        // Status colours
        "status-deployed":      "#32C850",
        "status-planned":       "#6B7280",
        "status-construction":  "#F59E0B",
        "status-decommissioned":"#EF4444",
        // UI
        "panel-bg":    "rgba(15, 20, 35, 0.92)",
        "panel-border":"rgba(255,255,255,0.08)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      boxShadow: {
        "panel": "0 4px 32px rgba(0,0,0,0.5)",
        "glow-green": "0 0 12px rgba(50,200,80,0.4)",
        "glow-cyan":  "0 0 16px rgba(0,230,255,0.5)",
      },
    },
  },
  plugins: [],
};
