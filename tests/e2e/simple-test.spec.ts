import { test, expect } from '@playwright/test';

test('simple homepage test', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Neuronode/);
  console.log('✅ Simple test passed');
}); 