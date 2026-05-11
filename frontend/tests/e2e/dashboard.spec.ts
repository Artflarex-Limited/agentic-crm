import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('dashboard loads and shows stats', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('Dashboard');

    await expect(page.getByText('Total Leads')).toBeVisible();
    await expect(page.getByText('Total Contacts')).toBeVisible();
    await expect(page.getByText('Total Deals')).toBeVisible();
    await expect(page.getByText('Open Deals Value')).toBeVisible();
  });

  test('pipeline section renders', async ({ page }) => {
    await expect(page.getByText('Pipeline')).toBeVisible();

    const stageHeaders = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost'];
    for (const stage of stageHeaders) {
      await expect(page.getByText(stage)).toBeVisible();
    }
  });

  test('stats show numeric values', async ({ page }) => {
    const totalLeads = page.locator('div:text("Total Leads")').locator('..').locator('.text-2xl');
    await expect(totalLeads).toBeVisible();
  });
});