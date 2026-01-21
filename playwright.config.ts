import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  reporter: [['html', { outputFolder: 'misc/playwright-report' }]],
  outputDir: 'misc/test-results',
  use: {
    baseURL: 'http://localhost:9002',
    headless: true,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'pnpm run dev',
    port: 9002,
    reuseExistingServer: !process.env.CI,
    env: {
      ...process.env,
      ENABLE_TEST_AUTH: 'true',
      FIRESTORE_EMULATOR_HOST: 'localhost:8080', 
    },
  },
});
