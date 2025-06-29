import { defineConfig, devices } from '@playwright/test';

/**
 * K3.3 Playwright Configuration
 * Enterprise-Grade E2E Testing Setup für Complete User Journey Validation
 */
export default defineConfig({
  // Test discovery
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',
  
  // Global test settings - OPTIMIZED
  timeout: 30 * 1000, // Reduced from 60s to 30s for faster execution
  expect: {
    timeout: 10 * 1000, // Reduced from 15s to 10s for UI assertions
  },
  
  // Test execution
  fullyParallel: false, // Sequential execution for more stable results
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0, // Reduced retries for faster feedback
  workers: 1, // Single worker for deterministic results
  
  // Reporting - OPTIMIZED FOR JSON OUTPUT
  reporter: [
    ['json', { outputFile: 'test-results-final.json' }],
    ['line'], // Cleaner console output
  ],
  
  // Global test configuration - ENHANCED FOR EDGE
  use: {
    baseURL: 'http://localhost:3000',
    
    // Enhanced browser settings for Edge compatibility
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure', 
    video: 'retain-on-failure',
    
    // Optimized timeouts for Edge browser
    actionTimeout: 15 * 1000, // Reduced from 30s to 15s
    navigationTimeout: 20 * 1000, // Reduced from 60s to 20s
    
    // Additional settings for better Edge compatibility
    bypassCSP: true, // Helps with Edge content security policies
    ignoreHTTPSErrors: true, // Ignore SSL issues during testing
  },

  // Cross-browser test projects - OPTIMIZED
  projects: [
    // Desktop browsers with optimized settings
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Additional Chrome-specific optimizations
        launchOptions: {
          args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
        }
      },
    },
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    {
      name: 'edge',
      use: { 
        ...devices['Desktop Edge'],
        viewport: { width: 1920, height: 1080 },
        // Enhanced Edge-specific settings
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
          ]
        },
        // Longer timeouts specifically for Edge
        actionTimeout: 20 * 1000,
        navigationTimeout: 25 * 1000,
      },
    },
    
    // Mobile devices - keeping original settings but with mobile exclusion capability
    {
      name: 'Mobile Chrome',
      use: { 
        ...devices['Pixel 5'],
        hasTouch: true,
      },
      // Can be excluded via grep pattern if needed
    },
    {
      name: 'Mobile Safari',
      use: { 
        ...devices['iPhone 13'],
        hasTouch: true,
      },
    },
    
    // Tablet and high-DPI optimized  
    {
      name: 'Tablet',
      use: { 
        ...devices['iPad Pro'],
        hasTouch: true,
      },
    },
    {
      name: 'chromium-high-dpi',
      use: { 
        ...devices['Desktop Chrome HiDPI'],
        hasTouch: true,
      },
    },
  ],

  // Development server - OPTIMIZED
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60 * 1000, // Reduced from 2 minutes to 1 minute
  },
}); 