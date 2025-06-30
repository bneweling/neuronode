/**
 * Centralized MockServiceLayer for E2E Tests
 * Provides deterministic API responses with consistent latency for stable testing
 */

import { Page, Route } from '@playwright/test';

export interface MockResponse {
  status: number;
  body: any;
  delay?: number;
}

export interface ChatQueryResponse {
  response: string;
  sources: string[];
  timestamp: string;
}

export interface GraphData {
  nodes: Array<{ id: string; label: string; type: string }>;
  edges: Array<{ from: string; to: string; label: string }>;
  stats: { totalNodes: number; totalEdges: number };
}

export interface UploadResponse {
  success: boolean;
  fileId: string;
  message: string;
}

export class MockServiceLayer {
  private static readonly DEFAULT_DELAY = 150; // Consistent 150ms response time
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Setup all standard API routes with deterministic responses
   */
  async setupStandardRoutes(): Promise<void> {
    await this.setupChatRoutes();
    await this.setupGraphRoutes();
    await this.setupUploadRoutes();
    await this.setupStatusRoutes();
  }

  /**
   * Chat API Routes with deterministic responses
   */
  async setupChatRoutes(): Promise<void> {
    // Chat query endpoint
    await this.page.route('**/api/chat/query*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          response: "Dies ist eine Mock-Antwort für Performance-Tests. Die KI-Analyse zeigt relevante Informationen basierend auf Ihrer Anfrage.",
          sources: ["document1.pdf", "document2.docx"],
          timestamp: new Date().toISOString(),
          processingTime: 145
        } as ChatQueryResponse
      });
    });

    // Chat history endpoint
    await this.page.route('**/api/chat/history*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          messages: [
            {
              id: "msg1",
              query: "Test-Anfrage",
              response: "Mock-Antwort für Chat-Historie",
              timestamp: new Date().toISOString()
            }
          ]
        }
      });
    });
  }

  /**
   * Graph API Routes with deterministic responses
   */
  async setupGraphRoutes(): Promise<void> {
    // Graph data endpoint
    await this.page.route('**/api/graph/data*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          nodes: [
            { id: "node1", label: "Konzept A", type: "concept" },
            { id: "node2", label: "Konzept B", type: "concept" },
            { id: "node3", label: "Dokument 1", type: "document" }
          ],
          edges: [
            { from: "node1", to: "node2", label: "related_to" },
            { from: "node2", to: "node3", label: "mentioned_in" }
          ],
          stats: { totalNodes: 15, totalEdges: 8 }
        } as GraphData
      });
    });

    // Graph statistics endpoint
    await this.page.route('**/api/graph/stats*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          totalNodes: 15,
          totalEdges: 8,
          connectedComponents: 1,
          centralNodes: ["node1", "node2"]
        }
      });
    });
  }

  /**
   * Upload API Routes with deterministic responses
   */
  async setupUploadRoutes(): Promise<void> {
    // File upload endpoint
    await this.page.route('**/api/upload*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          success: true,
          fileId: `mock-file-${Date.now()}`,
          message: "Datei erfolgreich hochgeladen und verarbeitet"
        } as UploadResponse,
        delay: 300 // Slightly longer for upload simulation
      });
    });

    // Upload progress endpoint
    await this.page.route('**/api/upload/progress*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          progress: 100,
          status: "completed",
          message: "Verarbeitung abgeschlossen"
        }
      });
    });
  }

  /**
   * Status and Health Check Routes
   */
  async setupStatusRoutes(): Promise<void> {
    // System status endpoint
    await this.page.route('**/api/status*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          status: "healthy",
          services: {
            database: "online",
            ai_service: "online",
            graph_engine: "online"
          },
          uptime: "99.9%"
        }
      });
    });
  }

  /**
   * Concurrent User Simulation for Load Testing
   */
  async setupConcurrentUserRoutes(userId: string): Promise<void> {
    // User-specific chat endpoint
    await this.page.route('**/api/chat/query*', async (route) => {
      await this.respondWithDelay(route, {
        status: 200,
        body: {
          response: `Mock-Antwort für Benutzer ${userId} - Performance Test erfolgreich`,
          sources: [`user_${userId}_doc1.pdf`],
          timestamp: new Date().toISOString(),
          userId: userId
        } as ChatQueryResponse
      });
    });
  }

  /**
   * WebSocket Event Simulation for Race Condition Testing
   */
  async simulateWebSocketEvent(eventType: string, data: any): Promise<void> {
    await this.page.evaluate(
      ({ eventType, data }) => {
        const event = new CustomEvent('websocket-update', {
          detail: { type: eventType, data: data }
        });
        window.dispatchEvent(event);
      },
      { eventType, data }
    );
  }

  /**
   * Core method to respond with consistent delay
   */
  private async respondWithDelay(route: Route, mockResponse: MockResponse): Promise<void> {
    const delay = mockResponse.delay || MockServiceLayer.DEFAULT_DELAY;
    
    // Add consistent delay for deterministic timing
    await new Promise(resolve => setTimeout(resolve, delay));
    
    await route.fulfill({
      status: mockResponse.status,
      contentType: 'application/json',
      body: JSON.stringify(mockResponse.body)
    });
  }

  /**
   * Error simulation for robustness testing
   */
  async simulateApiError(endpoint: string, errorCode: number = 500): Promise<void> {
    await this.page.route(endpoint, async (route) => {
      await route.fulfill({
        status: errorCode,
        contentType: 'application/json',
        body: JSON.stringify({
          error: "Simulated error for testing",
          code: errorCode,
          timestamp: new Date().toISOString()
        })
      });
    });
  }

  /**
   * Cleanup all mocked routes
   */
  async cleanup(): Promise<void> {
    await this.page.unrouteAll();
  }
}

/**
 * Factory function for easy MockServiceLayer creation
 */
export function createMockService(page: Page): MockServiceLayer {
  return new MockServiceLayer(page);
}

/**
 * Utility function for concurrent user simulation
 */
export async function setupConcurrentUserMocks(pages: Page[], userCount: number = 10): Promise<MockServiceLayer[]> {
  const mockServices: MockServiceLayer[] = [];
  
  for (let i = 0; i < Math.min(pages.length, userCount); i++) {
    const mockService = new MockServiceLayer(pages[i]);
    await mockService.setupStandardRoutes();
    await mockService.setupConcurrentUserRoutes(`user-${i + 1}`);
    mockServices.push(mockService);
  }
  
  return mockServices;
} 