import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e', timeout: 30000, retries: 0, workers: 1,
  use: { baseURL: process.env.CQ_WEB_URL || 'http://localhost:3000', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop-chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome' } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'], channel: 'chrome' } },
  ],
});
