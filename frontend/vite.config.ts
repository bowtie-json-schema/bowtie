import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // The real-world benchmark results (src/data/realWorldBenchmarks.ts):
      // the site serves them in production, but the benchmark's bucket
      // allows no other origins, so in development this server fetches them.
      "/jsonschema-benchmark": {
        target:
          "https://sourcemeta-research-jsonschema-benchmark.s3.eu-central-003.backblazeb2.com",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/jsonschema-benchmark/, "/latest"),
      },
    },
  },
  build: {
    sourcemap: true,
    target: ["es2022"],
    outDir: "build",
  },
});
