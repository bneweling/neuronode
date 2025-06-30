import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 K3.3 COMPREHENSIVE TESTING SETUP - Starting...');
  
  // Pre-warm the application and check if backend is available
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Test if frontend is reachable
    console.log('🌐 Testing frontend availability...');
    await page.goto(config.projects[0].use.baseURL || 'http://localhost:3000');
    await page.waitForSelector('body', { timeout: 30000 });
    console.log('✅ Frontend is ready');

    // Test if backend API is reachable (mock service should always be available)
    console.log('🔌 Testing backend API availability...');
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('/api/health');
        return { status: res.status, available: true };
      } catch (error) {
        // If API fails, we'll use Mock Service
        return { status: 200, available: false, mock: true };
      }
    });
    
    if (response.available) {
      console.log('✅ Backend API is ready');
    } else {
      console.log('⚠️  Using Mock Service for testing (Backend API not available)');
    }

    // Set up test data and clear any existing test state
    console.log('🧹 Clearing test state...');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    console.log('🎯 K3.3 Test Environment Setup Complete');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
