import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: true,
    target: ["es2022"],
    outDir: "build",
  },
  test: {
    environment: "jsdom",
  },
});
