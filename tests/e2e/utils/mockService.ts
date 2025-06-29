/**
 * E2E Testing MockServiceLayer
 * Centralized mocking for deterministic performance testing
 * 
 * This layer provides consistent, predictable API responses with configurable latency
 * for testing frontend performance in isolation from backend variability.
 */

// Extend Window interface for mock WebSocket functionality
declare global {
  interface Window {
    mockWebSocketEvents: Array<{ type: string; payload: any }>;
    MockWebSocket: typeof MockWebSocketClass;
  }
}

class MockWebSocketClass extends EventTarget {
  public url: string;
  public readyState: number;

  constructor(url: string) {
    super();
    this.url = url;
    this.readyState = 1; // OPEN
    
    // Listen for mock events
    window.addEventListener('mockWebSocketEvent', (event: Event) => {
      const customEvent = event as CustomEvent;
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(customEvent.detail)
      });
      this.dispatchEvent(messageEvent);
    });
  }
  
  send(data: string) {
    // Mock send - do nothing
  }
  
  close() {
    this.readyState = 3; // CLOSED
  }
}

export interface MockConfig {
  latency?: number;
  shouldFail?: boolean;
  responseData?: any;
}

export class MockServiceLayer {
  constructor(private page: any) {} // Using any to avoid playwright import issues

  /**
   * Setup deterministic mocking for all major API endpoints
   * with configurable latency for performance testing
   */
  async setupDeterministicMocks(config: {
    defaultLatency?: number;
    chatLatency?: number;
    uploadLatency?: number;
    graphLatency?: number;
  } = {}) {
    const {
      defaultLatency = 150, // Consistent baseline latency
      chatLatency = defaultLatency,
      uploadLatency = defaultLatency,
      graphLatency = defaultLatency
    } = config;

    // Chat API Mocking
    await this.page.route('**/api/chat/query*', async (route: any) => {
      await this.delay(chatLatency);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: "Mocked chat response for performance testing",
          sources: [],
          processing_time: chatLatency / 1000
        })
      });
    });

    // Document Upload API Mocking
    await this.page.route('**/api/documents/upload*', async (route: any) => {
      await this.delay(uploadLatency);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          document_id: "mock-doc-id",
          processing_status: "completed",
          upload_time: uploadLatency / 1000
        })
      });
    });

    // Graph Data API Mocking
    await this.page.route('**/api/knowledge-graph/data*', async (route: any) => {
      await this.delay(graphLatency);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          nodes: this.generateMockNodes(50), // Consistent node count for performance testing
          edges: this.generateMockEdges(75),
          statistics: {
            total_nodes: 50,
            total_edges: 75,
            documents: 5,
            concepts: 30,
            entities: 15
          }
        })
      });
    });

    // WebSocket mocking for real-time tests
    await this.page.route('**/ws/chat*', async (route: any) => {
      // Mock successful WebSocket connection
      await route.fulfill({
        status: 101,
        headers: { 'upgrade': 'websocket' }
      });
    });
  }

  /**
   * Setup concurrent user load testing with predictable responses
   */
  async setupConcurrentLoadMocks(config: {
    successRate?: number;
    responseLatency?: number;
  } = {}) {
    const { successRate = 0.8, responseLatency = 100 } = config;
    
    let requestCount = 0;

    await this.page.route('**/api/**', async (route: any) => {
      requestCount++;
      await this.delay(responseLatency);
      
      // Deterministic success/failure based on request count
      const shouldSucceed = (requestCount % 10) < (successRate * 10);
      
      if (shouldSucceed) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: "Mock successful response",
            request_id: requestCount
          })
        });
      } else {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: "Mock server error for load testing",
            request_id: requestCount
          })
        });
      }
    });
  }

  /**
   * Mock WebSocket push events for race condition testing
   */
  async mockWebSocketPush(eventType: string, payload: any = {}) {
    await this.page.evaluate(({ eventType, payload }: any) => {
      // Simulate WebSocket event directly in frontend context
      if (window.mockWebSocketEvents) {
        window.mockWebSocketEvents.push({ type: eventType, payload });
        
        // Trigger custom event that components can listen to
        window.dispatchEvent(new CustomEvent('mockWebSocketEvent', {
          detail: { type: eventType, payload }
        }));
      }
    }, { eventType, payload });
  }

  /**
   * Initialize mock WebSocket event system
   */
  async initializeMockWebSocket() {
    await this.page.evaluate(() => {
      window.mockWebSocketEvents = [];
      window.MockWebSocket = MockWebSocketClass;
    });
  }

  /**
   * Utility: Generate consistent mock nodes for testing
   */
  private generateMockNodes(count: number) {
    return Array.from({ length: count }, (_, i) => ({
      id: `node-${i}`,
      label: `Mock Node ${i}`,
      type: i % 3 === 0 ? 'document' : i % 3 === 1 ? 'concept' : 'entity',
      properties: {
        created_at: new Date().toISOString(),
        confidence: Math.random()
      }
    }));
  }

  /**
   * Utility: Generate consistent mock edges for testing
   */
  private generateMockEdges(count: number) {
    return Array.from({ length: count }, (_, i) => ({
      id: `edge-${i}`,
      source: `node-${i % 50}`,
      target: `node-${(i + 1) % 50}`,
      type: 'RELATES_TO',
      properties: {
        confidence: Math.random(),
        ai_generated: i % 2 === 0
      }
    }));
  }

  /**
   * Utility: Consistent delay for mocking
   */
  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Reset all route handlers
   */
  async resetMocks() {
    await this.page.unrouteAll();
  }
} 