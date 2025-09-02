import { defineConfig, devices } from '@playwright/test';

/**
 * ljwx系统Playwright E2E测试配置
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
  
  use: {
    baseURL: 'http://localhost:8080', // ljwx-admin前端地址
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: [
    {
      command: 'cd ../../ljwx-admin && pnpm dev',
      port: 8080,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd ../.. && ./run-local.sh',
      port: 3333,
      reuseExistingServer: !process.env.CI,
    }
  ],
});