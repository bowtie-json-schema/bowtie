import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    exclude: [
      ...configDefaults.exclude,
      "**/e2e/**",  // don't run playwright tests
    ],
    environment: "jsdom",
  },
});
