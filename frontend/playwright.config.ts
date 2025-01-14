import { defineConfig } from '@playwright/test';

const baseURL = 'http://localhost:5173';

export default defineConfig({
  testDir: 'e2e',
  webServer: {
    command: 'pnpm run start',
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
  },
  use: {
    baseURL,
  },
})
