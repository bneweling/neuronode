import { chromium, FullConfig } from '@playwright/test';

/**
 * K3.3 Global Setup for E2E Tests
 * Prepares mock backend, test data, and global test environment
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 K3.3 E2E Global Setup Starting...');

  // Start browser for setup tasks
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Wait for development server to be ready
    console.log('⏳ Waiting for development server at http://localhost:3000...');
    
    let retries = 30;
    while (retries > 0) {
      try {
        const response = await page.goto('http://localhost:3000');
        if (response?.ok()) {
          console.log('✅ Development server is ready');
          break;
        }
      } catch (error) {
        retries--;
        if (retries === 0) {
          throw new Error('Development server failed to start within timeout');
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    // Verify core components are loaded
    console.log('🔍 Verifying core application components...');
    
    // Check if main layout loads
    await page.waitForSelector('[data-testid="app-layout"]', { timeout: 10000 });
    console.log('✅ App layout loaded successfully');

    // Verify navigation elements
    const chatLink = page.locator('a[href="/chat"]');
    const uploadLink = page.locator('a[href="/upload"]');
    const graphLink = page.locator('a[href="/graph"]');
    
    await Promise.all([
      chatLink.waitFor({ timeout: 5000 }),
      uploadLink.waitFor({ timeout: 5000 }),
      graphLink.waitFor({ timeout: 5000 })
    ]);
    console.log('✅ Navigation elements verified');

    // Setup test environment variables
    process.env.E2E_TEST_MODE = 'true';
    process.env.E2E_MOCK_BACKEND = 'true';
    
    console.log('✅ K3.3 E2E Global Setup completed successfully');

  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

export default globalSetup; 