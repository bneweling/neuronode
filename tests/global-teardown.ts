import { FullConfig } from '@playwright/test';

/**
 * K3.3 Global Teardown for E2E Tests
 * Cleanup after all tests complete
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 K3.3 E2E Global Teardown Starting...');

  try {
    // Cleanup test environment variables
    delete process.env.E2E_TEST_MODE;
    delete process.env.E2E_MOCK_BACKEND;
    
    // Clear any test data or temporary files
    console.log('🗑️ Cleaning up test environment...');
    
    console.log('✅ K3.3 E2E Global Teardown completed successfully');

  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw - teardown failures shouldn't fail the test run
  }
}

export default globalTeardown; 