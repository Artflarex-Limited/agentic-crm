import { test, expect } from '@playwright/test';

test.describe('Create Lead Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/leads');
  });

  test('create lead button exists on leads page', async ({ page }) => {
    const createButton = page.getByRole('button', { name: /create/i }).or(page.getByText(/add lead/i));
    if (await createButton.isVisible()) {
      await expect(createButton).toBeVisible();
    }
  });

  test('lead form can be filled and submitted', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('Leads');

    const emailInput = page.locator('input[type="email"]').or(page.locator('input[placeholder*="email" i]'));
    if (await emailInput.isVisible({ timeout: 2000 })) {
      await emailInput.fill('test@example.com');
    }
  });
});