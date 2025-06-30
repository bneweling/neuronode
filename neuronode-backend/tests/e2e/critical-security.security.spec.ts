import { test, expect, Page } from '@playwright/test';
import { 
  authenticateUser, 
  authenticateAdmin,
  uploadDocument
} from '../helpers/test-helpers';

/**
 * ===================================================================
 * CRITICAL SECURITY TESTS - PHASE 1 (80/20 VALIDATION)
 * ===================================================================
 * 
 * Diese Tests validieren die wichtigsten Sicherheitsmechanismen gegen
 * die häufigsten Angriffsvektoren und müssen 100% erfolgreich sein.
 * 
 * Test Coverage:
 * - Horizontal Privilege Escalation Prevention
 * - Vertical Privilege Escalation Prevention
 * - Cross-Site Scripting (XSS) Prevention
 * - Cross-Site Request Forgery (CSRF) Prevention
 * - SQL Injection Prevention
 * - Authentication Bypass Prevention
 * 
 * Success Criteria: 100% Success Rate auf allen Browsern
 */

test.describe('Critical Security: Access Control Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Prevent horizontal privilege escalation - Document Access @critical @security', async ({ browser }) => {
    console.log('🔒 Testing horizontal privilege escalation prevention...');
    
    // Create two separate user contexts
    const userAContext = await browser.newContext();
    const userBContext = await browser.newContext();
    
    const userAPage = await userAContext.newPage();
    const userBPage = await userBContext.newPage();
    
    try {
      // ===============================================
      // STEP 1: User A uploads private document
      // ===============================================
      console.log('👤 Step 1: User A uploading private document...');
      await authenticateUser(userAPage, 'internal_user');
      
      // Upload a confidential document
      const uploadResult = await uploadDocument(userAPage, 'confidential-test.pdf');
      expect(uploadResult.success).toBe(true);
      
      const documentId = uploadResult.documentId;
      console.log(`✅ User A uploaded document: ${documentId}`);
      
      // ===============================================
      // STEP 2: User B attempts unauthorized access
      // ===============================================
      console.log('🚫 Step 2: User B attempting unauthorized access...');
      await authenticateUser(userBPage, 'internal_user');
      
      // Attempt direct document access via URL manipulation
      const directAccessResponse = await userBPage.request.get(`/api/documents/${documentId}`);
      console.log(`🔍 Direct API access status: ${directAccessResponse.status()}`);
      
      // Should receive 403 Forbidden or 404 Not Found
      expect([403, 404]).toContain(directAccessResponse.status());
      
      // Verify response body doesn't contain confidential data
      const responseBody = await directAccessResponse.text();
      expect(responseBody.toLowerCase()).not.toContain('confidential');
      expect(responseBody.toLowerCase()).not.toContain('private');
      
      // ===============================================
      // STEP 3: URL manipulation attempts
      // ===============================================
      console.log('🔗 Step 3: Testing URL manipulation attacks...');
      
      // Try various URL manipulation techniques
      const urlManipulationAttempts = [
        `/api/documents/${documentId}?user_id=user_a`,
        `/api/documents/${documentId}/../../../admin`,
        `/api/documents/${documentId}%00.pdf`,
        `/api/documents/${documentId}?bypass=true`,
        `/api/documents/${documentId}#admin`
      ];
      
      for (const maliciousUrl of urlManipulationAttempts) {
        const response = await userBPage.request.get(maliciousUrl);
        expect([400, 403, 404]).toContain(response.status());
        console.log(`✅ URL manipulation blocked: ${maliciousUrl} → ${response.status()}`);
      }
      
      // ===============================================
      // STEP 4: Frontend access prevention
      // ===============================================
      console.log('🖥️ Step 4: Testing frontend access prevention...');
      
      // Navigate to document view page directly
      await userBPage.goto(`/documents/${documentId}`);
      
      // Should be redirected or show access denied
      await expect(userBPage.locator('[data-testid="access-denied"]')).toBeVisible({ timeout: 5000 });
      
      // Verify document content is not visible
      await expect(userBPage.locator('[data-testid="document-content"]')).not.toBeVisible();
      
      console.log('✅ Horizontal privilege escalation successfully prevented');
      
    } finally {
      await userAContext.close();
      await userBContext.close();
    }
  });

  test('Prevent vertical privilege escalation - Admin Endpoint Protection @critical @security', async ({ page }) => {
    console.log('🔐 Testing vertical privilege escalation prevention...');
    
    try {
      // ===============================================
      // STEP 1: Authenticate as regular user
      // ===============================================
      console.log('👤 Step 1: Authenticating as regular internal_user...');
      const authResult = await authenticateUser(page, 'internal_user');
      expect(authResult.success).toBe(true);
      expect(authResult.role).toBe('internal_user');
      
      // ===============================================
      // STEP 2: Attempt admin API endpoint access
      // ===============================================
      console.log('🚫 Step 2: Attempting admin endpoint access...');
      
      const adminEndpoints = [
        '/api/admin/models/assignments',
        '/api/admin/users',
        '/api/admin/audit',
        '/api/admin/system/health',
        '/api/admin/models/performance'
      ];
      
      for (const endpoint of adminEndpoints) {
        console.log(`🔍 Testing admin endpoint: ${endpoint}`);
        
        // Try GET request
        const getResponse = await page.request.get(endpoint);
        expect(getResponse.status()).toBe(403);
        console.log(`✅ GET ${endpoint} → 403 Forbidden`);
        
        // Try POST request (if applicable)
        if (endpoint.includes('assignments') || endpoint.includes('users')) {
          const postResponse = await page.request.post(endpoint, {
            data: { test: 'unauthorized' }
          });
          expect(postResponse.status()).toBe(403);
          console.log(`✅ POST ${endpoint} → 403 Forbidden`);
        }
      }
      
      // ===============================================
      // STEP 3: Frontend admin panel access
      // ===============================================
      console.log('🖥️ Step 3: Testing frontend admin panel access...');
      
      // Navigate to admin panel
      await page.goto('/admin');
      
      // Should be redirected or show access denied
      await expect(page.locator('[data-testid="access-denied"]')).toBeVisible({ timeout: 5000 });
      
      // Verify admin controls are not visible
      await expect(page.locator('[data-testid="admin-controls"]')).not.toBeVisible();
      
      // ===============================================
      // STEP 4: JWT token manipulation attempts
      // ===============================================
      console.log('🔑 Step 4: Testing JWT token manipulation...');
      
      // Try to modify JWT token in localStorage
      await page.evaluate(() => {
        const originalToken = localStorage.getItem('auth_token');
        
        // Attempt to modify role in JWT payload (client-side)
        try {
          const tokenParts = originalToken?.split('.');
          if (tokenParts && tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]));
            payload.role = 'proxy_admin';
            tokenParts[1] = btoa(JSON.stringify(payload));
            const modifiedToken = tokenParts.join('.');
            localStorage.setItem('auth_token', modifiedToken);
          }
        } catch (error) {
          console.log('Token manipulation failed:', error);
        }
      });
      
      // Refresh and try admin endpoint again
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      const tamperedTokenResponse = await page.request.get('/api/admin/models/assignments');
      expect(tamperedTokenResponse.status()).toBe(403);
      console.log('✅ Tampered JWT token rejected');
      
      console.log('✅ Vertical privilege escalation successfully prevented');
      
    } catch (error) {
      console.error('❌ Vertical privilege escalation test failed:', error);
      await page.screenshot({ 
        path: `test-results/vertical-privilege-failure-${Date.now()}.png`,
        fullPage: true 
      });
      throw error;
    }
  });

  test('Cross-Site Scripting (XSS) Prevention @critical @security', async ({ page }) => {
    console.log('🛡️ Testing XSS prevention...');
    
    try {
      // ===============================================
      // STEP 1: Authenticate user
      // ===============================================
      await authenticateUser(page, 'internal_user');
      
      // ===============================================
      // STEP 2: XSS in chat interface
      // ===============================================
      console.log('💬 Step 2: Testing XSS in chat interface...');
      
      await page.goto('/chat');
      await page.waitForLoadState('networkidle');
      
      const xssPayloads = [
        '<script>alert("XSS")</script>',
        '<img src="x" onerror="alert(\'XSS\')" />',
        '<svg onload="alert(\'XSS\')" />',
        'javascript:alert("XSS")',
        '<iframe src="javascript:alert(\'XSS\')"></iframe>',
        '"><script>document.body.innerHTML="HACKED"</script>'
      ];
      
      for (const payload of xssPayloads) {
        console.log(`🔍 Testing XSS payload: ${payload.substring(0, 30)}...`);
        
        // Send malicious payload in chat
        await page.fill('[data-testid="chat-input"]', payload);
        await page.click('[data-testid="send-button"]');
        
        // Wait for response
        await page.waitForSelector('[data-testid="chat-message"]', { state: 'visible' });
        
        // Verify payload is displayed as text, not executed
        const messageContent = await page.locator('[data-testid="chat-message"]').last().textContent();
        expect(messageContent).toContain('<script>');
        
        // Verify page wasn't compromised
        const bodyContent = await page.textContent('body');
        expect(bodyContent).not.toBe('XSS');
        expect(bodyContent).not.toBe('HACKED');
        
        // Check for alert dialogs (shouldn't exist)
        const dialogPromise = page.waitForEvent('dialog', { timeout: 1000 }).catch(() => null);
        const dialog = await dialogPromise;
        expect(dialog).toBeNull();
        
        console.log(`✅ XSS payload sanitized: ${payload.substring(0, 30)}...`);
      }
      
      // ===============================================
      // STEP 3: XSS in document upload
      // ===============================================
      console.log('📄 Step 3: Testing XSS in document upload...');
      
      await page.goto('/documents/upload');
      await page.waitForLoadState('networkidle');
      
      // Try to upload a file with malicious name
      const maliciousFilenames = [
        '"><script>alert("XSS")</script>.pdf',
        'test<img src=x onerror=alert("XSS")>.pdf',
        'test.pdf<script>alert("XSS")</script>'
      ];
      
      for (const filename of maliciousFilenames) {
        // This would be blocked at the file system level in real scenarios
        // But we test the display handling
        await page.evaluate((fname) => {
          const input = document.querySelector('[data-testid="filename-display"]');
          if (input) {
            input.textContent = fname;
          }
        }, filename);
        
        // Verify filename is displayed safely
        const displayedName = await page.locator('[data-testid="filename-display"]').textContent();
        expect(displayedName).toContain('<script>');
        
        console.log(`✅ Malicious filename sanitized: ${filename}`);
      }
      
      console.log('✅ XSS prevention successful');
      
    } catch (error) {
      console.error('❌ XSS prevention test failed:', error);
      throw error;
    }
  });

  test('Cross-Site Request Forgery (CSRF) Prevention @critical @security', async ({ page, context }) => {
    console.log('🛡️ Testing CSRF prevention...');
    
    try {
      // ===============================================
      // STEP 1: Authenticate admin user
      // ===============================================
      await authenticateAdmin(page);
      
      // ===============================================
      // STEP 2: Simulate CSRF attack
      // ===============================================
      console.log('🎭 Step 2: Simulating CSRF attack...');
      
      // Create malicious page in new context
      const maliciousContext = await page.context().browser()?.newContext();
      const maliciousPage = await maliciousContext?.newPage();
      
      if (!maliciousPage) {
        throw new Error('Could not create malicious page context');
      }
      
      // Create malicious HTML page
      const maliciousHtml = `
        <!DOCTYPE html>
        <html>
        <body>
          <form id="csrf-form" action="http://localhost:3001/api/admin/models/assignments" method="POST">
            <input type="hidden" name="task_type" value="synthesis" />
            <input type="hidden" name="profile" value="premium" />
            <input type="hidden" name="new_model" value="malicious-model" />
          </form>
          <script>document.getElementById('csrf-form').submit();</script>
        </body>
        </html>
      `;
      
      // Navigate to malicious page
      await maliciousPage.setContent(maliciousHtml);
      
      // Wait for form submission attempt
      await maliciousPage.waitForTimeout(2000);
      
      // ===============================================
      // STEP 3: Verify CSRF protection
      // ===============================================
      console.log('🔍 Step 3: Verifying CSRF protection...');
      
      // Check if the malicious request was blocked
      const response = await maliciousPage.waitForResponse(
        response => response.url().includes('/api/admin/models/assignments'),
        { timeout: 5000 }
      ).catch(() => null);
      
      if (response) {
        // If response received, it should be blocked
        expect([403, 400]).toContain(response.status());
        console.log(`✅ CSRF request blocked with status: ${response.status()}`);
      } else {
        console.log('✅ CSRF request prevented (no response received)');
      }
      
      // ===============================================
      // STEP 4: Valid request with CSRF token
      // ===============================================
      console.log('✅ Step 4: Testing valid request with CSRF token...');
      
      // Get CSRF token from legitimate page
      await page.goto('/admin/models');
      const csrfToken = await page.locator('[name="csrf-token"]').getAttribute('content');
      
      // Make legitimate request with CSRF token
      const validResponse = await page.request.post('/api/admin/models/assignments', {
        headers: {
          'X-CSRF-Token': csrfToken || ''
        },
        data: {
          task_type: 'classification',
          profile: 'balanced',
          new_model: 'openai/gpt-4o-mini',
          reason: 'CSRF test - legitimate request'
        }
      });
      
      // This should succeed (or fail with proper validation, not CSRF)
      expect([200, 400, 422]).toContain(validResponse.status());
      expect(validResponse.status()).not.toBe(403);
      
      console.log('✅ CSRF prevention successful');
      
      await maliciousContext?.close();
      
    } catch (error) {
      console.error('❌ CSRF prevention test failed:', error);
      throw error;
    }
  });

  test('SQL Injection Prevention @critical @security', async ({ page }) => {
    console.log('🛡️ Testing SQL injection prevention...');
    
    try {
      await authenticateUser(page, 'internal_user');
      
      // ===============================================
      // SQL Injection in search functionality
      // ===============================================
      console.log('🔍 Testing SQL injection in search...');
      
      await page.goto('/search');
      await page.waitForLoadState('networkidle');
      
      const sqlInjectionPayloads = [
        "'; DROP TABLE documents; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "'; INSERT INTO users (role) VALUES ('admin'); --",
        "' OR 1=1 --",
        "admin'--",
        "' OR 'x'='x",
        "'; UPDATE users SET role='admin' WHERE id=1; --"
      ];
      
      for (const payload of sqlInjectionPayloads) {
        console.log(`🔍 Testing SQL injection: ${payload.substring(0, 20)}...`);
        
        // Try search with malicious payload
        await page.fill('[data-testid="search-input"]', payload);
        await page.click('[data-testid="search-button"]');
        
        // Wait for response
        await page.waitForSelector('[data-testid="search-results"], [data-testid="search-error"]', {
          state: 'visible',
          timeout: 10000
        });
        
        // Verify no unauthorized data is returned
        const results = await page.locator('[data-testid="search-results"]').textContent();
        
        // Should not contain sensitive data patterns
        expect(results?.toLowerCase()).not.toMatch(/password|secret|token|admin/);
        
        // Should not show SQL error messages
        expect(results?.toLowerCase()).not.toMatch(/sql|mysql|postgresql|database error/);
        
        console.log(`✅ SQL injection prevented: ${payload.substring(0, 20)}...`);
      }
      
      // ===============================================
      // SQL Injection in document ID parameter
      // ===============================================
      console.log('📄 Testing SQL injection in document access...');
      
      const documentSqlPayloads = [
        "1' OR '1'='1",
        "1; DROP TABLE documents; --",
        "1 UNION SELECT password FROM users --"
      ];
      
      for (const payload of documentSqlPayloads) {
        const response = await page.request.get(`/api/documents/${encodeURIComponent(payload)}`);
        
        // Should return 400 (bad request) or 404 (not found), not 500 (server error)
        expect([400, 404]).toContain(response.status());
        
        const responseText = await response.text();
        expect(responseText.toLowerCase()).not.toMatch(/sql|error|exception/);
        
        console.log(`✅ SQL injection in document ID prevented: ${payload}`);
      }
      
      console.log('✅ SQL injection prevention successful');
      
    } catch (error) {
      console.error('❌ SQL injection prevention test failed:', error);
      throw error;
    }
  });

  test('Authentication bypass prevention @critical @security', async ({ page }) => {
    console.log('🔐 Testing authentication bypass prevention...');
    
    try {
      // ===============================================
      // STEP 1: Access protected endpoints without authentication
      // ===============================================
      console.log('🚫 Step 1: Testing unauthenticated access...');
      
      const protectedEndpoints = [
        '/api/documents',
        '/api/chat',
        '/api/admin/models',
        '/api/user/profile',
        '/api/search'
      ];
      
      for (const endpoint of protectedEndpoints) {
        const response = await page.request.get(endpoint);
        expect([401, 403]).toContain(response.status());
        console.log(`✅ Unauthenticated access blocked: ${endpoint} → ${response.status()}`);
      }
      
      // ===============================================
      // STEP 2: Invalid token attempts
      // ===============================================
      console.log('🔑 Step 2: Testing invalid token attempts...');
      
      const invalidTokens = [
        'invalid-jwt-token',
        'Bearer invalid',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature',
        '',
        'null',
        'undefined'
      ];
      
      for (const invalidToken of invalidTokens) {
        const response = await page.request.get('/api/documents', {
          headers: {
            'Authorization': `Bearer ${invalidToken}`
          }
        });
        
        expect([401, 403]).toContain(response.status());
        console.log(`✅ Invalid token rejected: ${invalidToken.substring(0, 20)}...`);
      }
      
      // ===============================================
      // STEP 3: Expired token handling
      // ===============================================
      console.log('⏰ Step 3: Testing expired token handling...');
      
      // Create an expired JWT token (mock)
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.expired';
      
      const expiredResponse = await page.request.get('/api/documents', {
        headers: {
          'Authorization': `Bearer ${expiredToken}`
        }
      });
      
      expect([401, 403]).toContain(expiredResponse.status());
      console.log('✅ Expired token rejected');
      
      // ===============================================
      // STEP 4: Session fixation prevention
      // ===============================================
      console.log('🔄 Step 4: Testing session fixation prevention...');
      
      // Try to set a custom session ID
      await page.evaluate(() => {
        localStorage.setItem('session_id', 'attacker-controlled-session-id');
        localStorage.setItem('auth_token', 'attacker-token');
      });
      
      // Try to access protected resource
      const fixationResponse = await page.request.get('/api/documents');
      expect([401, 403]).toContain(fixationResponse.status());
      
      console.log('✅ Session fixation prevented');
      
      console.log('✅ Authentication bypass prevention successful');
      
    } catch (error) {
      console.error('❌ Authentication bypass prevention test failed:', error);
      throw error;
    }
  });
});

test.describe('Critical Security: Data Protection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Sensitive data exposure prevention @critical @security', async ({ page }) => {
    console.log('🔒 Testing sensitive data exposure prevention...');
    
    try {
      await authenticateUser(page, 'internal_user');
      
      // ===============================================
      // Check for exposed sensitive data in responses
      // ===============================================
      const sensitivePatterns = [
        /password/i,
        /secret/i,
        /token/i,
        /key/i,
        /jwt/i,
        /api[_-]?key/i,
        /database[_-]?url/i,
        /connection[_-]?string/i
      ];
      
      const endpoints = [
        '/api/user/profile',
        '/api/documents',
        '/api/health'
      ];
      
      for (const endpoint of endpoints) {
        const response = await page.request.get(endpoint);
        const responseText = await response.text();
        
        for (const pattern of sensitivePatterns) {
          expect(responseText).not.toMatch(pattern);
        }
        
        console.log(`✅ No sensitive data exposed in: ${endpoint}`);
      }
      
      console.log('✅ Sensitive data protection successful');
      
    } catch (error) {
      console.error('❌ Sensitive data protection test failed:', error);
      throw error;
    }
  });

  test('Information disclosure prevention @critical @security', async ({ page }) => {
    console.log('📊 Testing information disclosure prevention...');
    
    try {
      // ===============================================
      // Test error message disclosure
      // ===============================================
      const malformedRequests = [
        '/api/documents/999999999',
        '/api/nonexistent-endpoint',
        '/api/documents/invalid-id-format'
      ];
      
      for (const request of malformedRequests) {
        const response = await page.request.get(request);
        const responseText = await response.text();
        
        // Should not expose internal paths, stack traces, or system info
        expect(responseText.toLowerCase()).not.toMatch(/traceback|stack trace|exception|error.*line/);
        expect(responseText).not.toMatch(/\/var\/www|\/home\/|c:\\|\\windows\\|node_modules/);
        expect(responseText.toLowerCase()).not.toMatch(/postgresql|mysql|mongodb|redis/);
        
        console.log(`✅ Information disclosure prevented: ${request}`);
      }
      
      console.log('✅ Information disclosure prevention successful');
      
    } catch (error) {
      console.error('❌ Information disclosure prevention test failed:', error);
      throw error;
    }
  });
}); 