import { test, expect } from '@playwright/test';

test.describe('Agent Status Page', () => {
  test('agent page renders when navigiated directly', async ({ page }) => {
    await page.goto('/agents');
  });
});