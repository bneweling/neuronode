import { test, expect, Page } from '@playwright/test';
import { 
  authenticateUser, 
  authenticateAdmin,
  uploadDocument,
  monitorWebSocketUpdates,
  askQuestion,
  clickGraphLink,
  verifyGraphNodes,
  clickGraphEdge,
  verifyCoTDialog,
  navigateToLiteLLM,
  changeModelAssignment,
  askPremiumQuestion,
  verifyAuditLog
} from '../helpers/test-helpers';

/**
 * ===================================================================
 * CRITICAL USER JOURNEY TESTS - PHASE 1 (80/20 VALIDATION)
 * ===================================================================
 * 
 * Diese Tests validieren die wichtigsten Wertschöpfungsketten für 
 * Endnutzer und müssen in unter 60 Sekunden auf allen Browsern 
 * fehlerfrei funktionieren.
 * 
 * Test Coverage:
 * - Document-to-Insight Workflow (Kern-Value-Chain)
 * - Dynamic Model Switch Workflow (Admin-Journey)
 * 
 * Success Criteria: 100% Success Rate auf Chrome & Firefox
 */

test.describe('Critical User Journey: Document-to-Insight', () => {
  test.beforeEach(async ({ page }) => {
    // Reset test environment
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Complete workflow: Upload → Processing → Query → Graph → CoT @critical', async ({ page }) => {
    const startTime = Date.now();
    
    try {
      // ===============================================
      // STEP 1: User Authentication (internal_user)
      // ===============================================
      console.log('🔑 Step 1: Authenticating internal_user...');
      await authenticateUser(page, 'internal_user');
      
      // Verify successful login
      await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-indicator"]')).toContainText('internal_user');
      
      // ===============================================
      // STEP 2: Document Upload (BSI-Standard PDF)
      // ===============================================
      console.log('📄 Step 2: Uploading complex PDF document...');
      const documentId = await uploadDocument(page, 'bsi-standard-complex.pdf');
      
      // Verify upload initiated
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-filename"]')).toContainText('bsi-standard-complex.pdf');
      
      // ===============================================
      // STEP 3: Real-time Processing Monitoring
      // ===============================================
      console.log('⚡ Step 3: Monitoring WebSocket status updates...');
      const processingComplete = await monitorWebSocketUpdates(page, 'PROCESSING_COMPLETE', {
        timeout: 45000, // 45 seconds max processing time
        expectedStages: ['UPLOAD_COMPLETE', 'EXTRACTION_STARTED', 'GRAPH_BUILDING', 'PROCESSING_COMPLETE']
      });
      
      expect(processingComplete).toBe(true);
      
      // Verify processing completion UI
      await expect(page.locator('[data-testid="processing-status"]')).toContainText('Verarbeitung abgeschlossen');
      await expect(page.locator('[data-testid="document-ready-indicator"]')).toBeVisible();
      
      // ===============================================
      // STEP 4: Context-aware Query Processing
      // ===============================================
      console.log('💬 Step 4: Asking document-specific question...');
      const questionText = 'Was sind die Hauptanforderungen für Kryptographie nach diesem BSI-Standard?';
      const response = await askQuestion(page, questionText);
      
      // Verify intelligent response with document context
      expect(response.text).toContain('BSI');
      expect(response.text).toContain('Kryptographie');
      expect(response.text).toContain('Anforderungen');
      
      // Verify response metadata
      expect(response.responseTime).toBeLessThan(10000); // <10s response time
      expect(response.documentReferences).toContain(documentId);
      
      // ===============================================
      // STEP 5: Graph Visualization Navigation
      // ===============================================
      console.log('🌐 Step 5: Navigating to graph visualization...');
      await clickGraphLink(page);
      
      // Wait for graph to render
      await page.waitForSelector('[data-testid="graph-container"]', { state: 'visible' });
      await page.waitForTimeout(2000); // Allow graph rendering
      
      // Verify graph contains document-derived nodes
      const graphNodes = await verifyGraphNodes(page, [
        'BSI',
        'Kryptographie', 
        'Anforderungen',
        'Standard',
        'Sicherheit'
      ]);
      
      expect(graphNodes.foundNodes.length).toBeGreaterThanOrEqual(3);
      expect(graphNodes.missingNodes.length).toBeLessThanOrEqual(2);
      
      // ===============================================
      // STEP 6: Chain-of-Thought Dialog Verification
      // ===============================================
      console.log('🧠 Step 6: Testing Chain-of-Thought functionality...');
      await clickGraphEdge(page, 'IMPLEMENTS');
      
      // Verify CoT dialog appears
      const cotDialog = await verifyCoTDialog(page);
      expect(cotDialog.isVisible).toBe(true);
      expect(cotDialog.reasoning).toContain('IMPLEMENTS');
      expect(cotDialog.confidence).toBeGreaterThan(0.8);
      
      // ===============================================
      // SUCCESS METRICS VALIDATION
      // ===============================================
      const totalTime = Date.now() - startTime;
      console.log(`✅ Complete workflow completed in ${totalTime}ms`);
      
      // Must complete in under 60 seconds
      expect(totalTime).toBeLessThan(60000);
      
      // Log success metrics
      await page.evaluate((metrics) => {
        console.log('SUCCESS METRICS:', metrics);
      }, {
        totalTime,
        documentId,
        responseTime: response.responseTime,
        graphNodesFound: graphNodes.foundNodes.length,
        cotConfidence: cotDialog.confidence
      });
      
    } catch (error) {
      console.error('❌ Critical User Journey FAILED:', error);
      
      // Capture failure context
      await page.screenshot({ path: `test-results/critical-journey-failure-${Date.now()}.png`, fullPage: true });
      
      throw error;
    }
  });

  test('Workflow resilience: Network interruption recovery @critical', async ({ page }) => {
    console.log('🌐 Testing network resilience during document processing...');
    
    // Start document upload
    await authenticateUser(page, 'internal_user');
    const uploadPromise = uploadDocument(page, 'test-document.pdf');
    
    // Simulate network interruption
    await page.route('**/*', route => route.abort());
    await page.waitForTimeout(3000);
    
    // Restore network
    await page.unroute('**/*');
    
    // Verify recovery
    await expect(page.locator('[data-testid="connection-restored"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="upload-resumed"]')).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Critical Admin Journey: Dynamic Model Assignment', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Dynamic model switch without service restart @critical', async ({ page, context }) => {
    const startTime = Date.now();
    
    try {
      // ===============================================
      // STEP 1: Admin Authentication & LiteLLM Access
      // ===============================================
      console.log('👑 Step 1: Admin authentication...');
      await authenticateAdmin(page);
      
      // Verify admin privileges
      await expect(page.locator('[data-testid="admin-panel-access"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-indicator"]')).toContainText('proxy_admin');
      
      // ===============================================
      // STEP 2: LiteLLM Model Management UI
      // ===============================================
      console.log('⚙️ Step 2: Accessing LiteLLM management interface...');
      
      // Open LiteLLM in new tab/context
      const adminPage = await context.newPage();
      await navigateToLiteLLM(adminPage, process.env.TEST_LITELLM_URL || 'http://localhost:4000');
      
      // Verify LiteLLM UI access
      await expect(adminPage.locator('[data-testid="litellm-dashboard"]')).toBeVisible();
      
      // ===============================================
      // STEP 3: Model Assignment Change
      // ===============================================
      console.log('🔄 Step 3: Changing model assignment...');
      const assignmentChange = await changeModelAssignment(adminPage, {
        alias: 'synthesis_premium',
        oldModel: 'openai/gpt-4o',
        newModel: 'anthropic/claude-3-5-sonnet',
        reason: 'Performance optimization test'
      });
      
      expect(assignmentChange.success).toBe(true);
      expect(assignmentChange.auditId).toBeDefined();
      
      // Verify assignment update in UI
      await expect(adminPage.locator('[data-testid="assignment-updated"]')).toBeVisible();
      await expect(adminPage.locator('[data-testid="current-model"]')).toContainText('claude-3-5-sonnet');
      
      // ===============================================
      // STEP 4: User Experience Validation
      // ===============================================
      console.log('👤 Step 4: Validating user experience with new model...');
      
      // Switch back to user page
      await page.bringToFront();
      
      // Logout and re-login as regular user
      await page.locator('[data-testid="user-menu"]').click();
      await page.locator('[data-testid="logout-button"]').click();
      await authenticateUser(page, 'internal_user');
      
      // Ask question that triggers premium model
      const premiumResponse = await askPremiumQuestion(page, {
        text: 'Erstelle eine komplexe Analyse der Cybersicherheitstrends für 2024',
        expectedModel: 'synthesis_premium'
      });
      
      expect(premiumResponse.success).toBe(true);
      expect(premiumResponse.responseTime).toBeLessThan(15000); // <15s response time
      
      // ===============================================
      // STEP 5: Audit Log Verification
      // ===============================================
      console.log('📋 Step 5: Verifying audit logs...');
      const auditVerification = await verifyAuditLog(adminPage, {
        requestId: premiumResponse.requestId,
        expectedModel: 'anthropic/claude-3-5-sonnet',
        auditId: assignmentChange.auditId
      });
      
      expect(auditVerification.modelUsed).toBe('anthropic/claude-3-5-sonnet');
      expect(auditVerification.auditEntryFound).toBe(true);
      expect(auditVerification.rbacCompliant).toBe(true);
      
      // ===============================================
      // SUCCESS METRICS VALIDATION
      // ===============================================
      const totalTime = Date.now() - startTime;
      console.log(`✅ Dynamic model switch completed in ${totalTime}ms`);
      
      // Must complete without service restart
      expect(totalTime).toBeLessThan(30000); // <30s total time
      
      // Verify no service downtime
      const healthCheck = await page.request.get('/api/health');
      expect(healthCheck.ok()).toBe(true);
      
      await adminPage.close();
      
    } catch (error) {
      console.error('❌ Admin Journey FAILED:', error);
      await page.screenshot({ path: `test-results/admin-journey-failure-${Date.now()}.png`, fullPage: true });
      throw error;
    }
  });

  test('Model assignment rollback capability @critical', async ({ page }) => {
    console.log('🔙 Testing model assignment rollback...');
    
    await authenticateAdmin(page);
    
    // Make initial assignment change
    const originalAssignment = await changeModelAssignment(page, {
      alias: 'classification_balanced',
      newModel: 'openai/gpt-4o-mini'
    });
    
    // Rollback assignment
    const rollback = await changeModelAssignment(page, {
      alias: 'classification_balanced', 
      newModel: originalAssignment.previousModel,
      reason: 'Test rollback'
    });
    
    expect(rollback.success).toBe(true);
    
    // Verify rollback in audit log
    const auditCheck = await verifyAuditLog(page, {
      auditId: rollback.auditId,
      action: 'rollback'
    });
    
    expect(auditCheck.auditEntryFound).toBe(true);
  });
});

test.describe('Critical Workflow: Concurrent User Sessions', () => {
  test('Multiple users simultaneous access @critical', async ({ browser }) => {
    console.log('👥 Testing concurrent user sessions...');
    
    // Create 5 concurrent user contexts
    const contexts = await Promise.all(
      Array.from({ length: 5 }, () => browser.newContext())
    );
    
    const pages = await Promise.all(
      contexts.map(context => context.newPage())
    );
    
    try {
      // Authenticate all users simultaneously
      await Promise.all(
        pages.map((page, index) => 
          authenticateUser(page, `test_user_${index + 1}`)
        )
      );
      
      // Each user uploads a document simultaneously
      const uploadPromises = pages.map((page, index) =>
        uploadDocument(page, `test-doc-${index + 1}.pdf`)
      );
      
      const results = await Promise.all(uploadPromises);
      
      // Verify all uploads succeeded
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
        console.log(`✅ User ${index + 1} upload successful: ${result.documentId}`);
      });
      
    } finally {
      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    }
  });
}); 