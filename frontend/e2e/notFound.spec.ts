import { test, expect } from '@playwright/test';

test('shows 404 page for non-existent routes', async ({ page }) => {
  await page.goto('/#/non-existent-route');
  await expect(page.getByText('Page Not Found')).toBeVisible();
});
