// playwright.config.js — minimal config for API tests
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.js',
  timeout: 30_000,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.API_BASE_URL || 'http://127.0.0.1:8000',
    extraHTTPHeaders: { 'Content-Type': 'application/json' },
  },
});
