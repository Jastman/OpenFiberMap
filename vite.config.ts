import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // vite-plugin-cesium handles:
    //  - Copying Cesium static assets (Workers, ThirdParty, Assets, Widgets) to dist/
    //  - Setting CESIUM_BASE_URL correctly for dev + production
    //  - Externalising large Cesium chunks properly
    cesium(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    // Cesium ships large static files; raise the warning threshold
    chunkSizeWarningLimit: 3000,
  },
  // Make public/data/ available at /data/
  publicDir: "public",
  base: "./",
});
