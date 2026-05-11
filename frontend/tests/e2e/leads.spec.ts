import { test, expect } from '@playwright/test';

test.describe('Leads Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/leads');
  });

  test('leads page renders with filter section', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('Leads');
    await expect(page.getByText('Filters')).toBeVisible();
  });

  test('leads table renders columns', async ({ page }) => {
    await expect(page.getByText('Name')).toBeVisible();
    await expect(page.getByText('Email')).toBeVisible();
    await expect(page.getByText('Company')).toBeVisible();
    await expect(page.getByText('Source')).toBeVisible();
    await expect(page.getText('Stage')).toBeVisible();
    await expect(page.getByText('Score')).toBeVisible();
  });

  test('empty state shows when no leads', async ({ page }) => {
    await expect(page.getByText('No leads found')).toBeVisible();
  });

  test('search input is functional', async ({ page }) => {
    const searchInput = page.locator('input[placeholder="Search leads..."]');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('test');
    await page.waitForTimeout(400);
  });

  test('stage filter dropdown works', async ({ page }) => {
    const stageSelect = page.locator('select').first();
    await expect(stageSelect).toBeVisible();
  });
});