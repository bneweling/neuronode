import { defineConfig, devices } from '@playwright/test';

/**
 * Enterprise Playwright Configuration for KI-Wissenssystem
 * Cross-Browser Testing Matrix for Production Readiness Validation
 * 
 * Test Coverage:
 * - 4 Desktop Browsers (Chrome, Firefox, Safari, Edge)
 * - 2 Mobile Browsers (Chrome Mobile, Safari Mobile)
 * - Accessibility Testing (WCAG 2.1 AA)
 * - Performance Testing
 * - Security Testing
 */

export default defineConfig({
  // ===================================================================
  // TEST CONFIGURATION
  // ===================================================================
  testDir: './e2e',
  
  // Timeout Configuration - Erhöht für E2E Robustheit
  timeout: 90 * 1000, // 90 seconds per test für komplexe Workflows
  expect: {
    timeout: 15 * 1000, // 15 seconds for assertions
  },
  
  // Test Execution Configuration
  fullyParallel: !process.env.DEBUG, // Sequential in debug mode
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 3 : 2, // Mehr Retries für Stabilität
  workers: process.env.CI ? 2 : (process.env.DEBUG ? 1 : undefined), // Single worker in debug
  
  // Reporter Configuration - Optimiert für Playbook Execution
  reporter: process.env.DEBUG ? [
    ['line'], // Debug: nur Line Reporter
    ['json', { outputFile: '../test-results/debug-results.json' }],
  ] : [
    ['line'], // Primärer Reporter für Live-Monitoring
    ['json', { outputFile: '../test-results/results.json' }], // JSON für Analyse
    ['html', { outputFolder: '../playwright-report', open: 'never' }], // HTML für Details
    ['junit', { outputFile: '../test-results/results.xml' }], // CI Integration
  ],
  
  // Global Configuration - Optimiert für Playbook Execution
  use: {
    // Base URL for all tests
    baseURL: process.env.TEST_FRONTEND_URL || 'http://localhost:3001',
    
    // Headfull-Konfiguration für bessere Sichtbarkeit
    headless: process.env.CI ? true : false, // Headfull in lokaler Ausführung
    slowMo: process.env.DEBUG ? 1000 : 500, // Langsamere Ausführung für Beobachtung
    
    // Tracing and Screenshots - Erweitert für Debugging
    trace: process.env.DEBUG ? 'on' : 'retain-on-failure',
    screenshot: process.env.DEBUG ? 'on' : 'only-on-failure',
    video: process.env.DEBUG ? 'on' : 'retain-on-failure',
    
    // Browser Configuration - Robuste Timeouts
    actionTimeout: 20 * 1000, // 20 seconds for actions
    navigationTimeout: 45 * 1000, // 45 seconds for navigation
    
    // Test Data
    storageState: undefined, // No persistent auth state
    
    // Network Configuration
    extraHTTPHeaders: {
      'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
      'User-Agent': 'KI-Wissenssystem-E2E-Test/1.0',
    },
    
    // Accessibility Configuration
    colorScheme: 'light',
    reducedMotion: 'reduce',
    
    // Enhanced Viewport für Desktop Tests
    viewport: { width: 1920, height: 1080 },
  },

  // ===================================================================
  // ENTERPRISE BROWSER MATRIX
  // ===================================================================
  projects: [
    // ===================================
    // PHASE 1: CRITICAL BROWSERS (80/20)
    // ===================================
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        contextOptions: {
          permissions: ['clipboard-read', 'clipboard-write'],
        },
      },
      testMatch: /.*\.critical\.spec\.ts/,
    },
    
    {
      name: 'firefox-desktop',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 },
      },
      testMatch: /.*\.critical\.spec\.ts/,
    },

    // ===================================
    // PHASE 2: COMPREHENSIVE COVERAGE
    // ===================================
    {
      name: 'webkit-desktop',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    
    {
      name: 'edge-desktop',
      use: { 
        ...devices['Desktop Edge'],
        viewport: { width: 1920, height: 1080 },
      },
    },

    // Mobile Browser Matrix
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5'],
      },
      testMatch: /.*\.mobile\.spec\.ts/,
    },
    
    {
      name: 'mobile-safari',
      use: { 
        ...devices['iPhone 12'],
      },
      testMatch: /.*\.mobile\.spec\.ts/,
    },

    // ===================================
    // PERFORMANCE TESTING
    // ===================================
    {
      name: 'performance-testing',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Performance-specific settings
        launchOptions: {
          args: [
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
          ],
        },
      },
      testMatch: /.*\.performance\.spec\.ts/,
    },

    // ===================================
    // ACCESSIBILITY TESTING
    // ===================================
    {
      name: 'accessibility-testing',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Accessibility-specific settings
        colorScheme: 'dark', // Test dark mode
        reducedMotion: 'reduce',
        forcedColors: 'active',
      },
      testMatch: /.*\.accessibility\.spec\.ts/,
    },

    // ===================================
    // SECURITY TESTING
    // ===================================
    {
      name: 'security-testing',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Security-specific settings
        contextOptions: {
          permissions: [], // No permissions granted
          strictSelectors: true,
        },
      },
      testMatch: /.*\.security\.spec\.ts/,
    },
  ],

  // ===================================================================
  // TEST ENVIRONMENT SETUP
  // ===================================================================
  globalSetup: require.resolve('./global-setup'),
  globalTeardown: require.resolve('./global-teardown'),

  // Web Server Configuration (for local development)
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes
  },
});

// ===================================================================
// ENVIRONMENT-SPECIFIC OVERRIDES
// ===================================================================

// CI Environment Optimizations
if (process.env.CI) {
  module.exports.use = {
    ...module.exports.use,
    // Reduce visual artifacts in CI
    video: 'off',
    screenshot: 'only-on-failure',
    trace: 'off',
  };
  
  // Optimize for CI performance
  module.exports.projects = module.exports.projects.filter(
    project => ['chromium-desktop', 'firefox-desktop'].includes(project.name)
  );
}

// Debug Mode Configuration
if (process.env.DEBUG) {
  module.exports.use = {
    ...module.exports.use,
    headless: false,
    slowMo: 1000,
    video: 'on',
    trace: 'on',
  };
  
  // Single browser for debugging
  module.exports.projects = [
    {
      name: 'debug-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    }
  ];
}

// ===================================================================
// TEST EXECUTION PATTERNS
// ===================================================================

/*
USAGE EXAMPLES:

# Phase 1: Critical Tests (80/20 Rule)
npx playwright test --grep="critical" --project="chromium-desktop,firefox-desktop"

# Phase 2: Full Cross-Browser Suite
npx playwright test --project="chromium-desktop,firefox-desktop,webkit-desktop,edge-desktop"

# Performance Testing
npx playwright test --grep="performance" --project="performance-testing"

# Security Testing
npx playwright test --grep="security" --project="security-testing"

# Accessibility Testing
npx playwright test --grep="accessibility" --project="accessibility-testing"

# Mobile Testing
npx playwright test --project="mobile-chrome,mobile-safari"

# Debug Mode
DEBUG=1 npx playwright test --grep="critical" --headed --project="debug-chrome"

# CI Mode (Optimized)
CI=1 npx playwright test
*/ 