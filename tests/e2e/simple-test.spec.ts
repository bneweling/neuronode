import { test, expect } from '@playwright/test';

test('simple homepage test', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/KI-Wissenssystem/);
  console.log('✅ Simple test passed');
}); 