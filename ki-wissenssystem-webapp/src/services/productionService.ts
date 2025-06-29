/**
 * Production API Service
 * Communicates with the real backend API
 */

import { KIWissenssystemAPI, GraphNodeData, GraphEdgeData } from '@/lib/api'

interface ChatResponseWithMetadata {
  message: string
  metadata?: Record<string, unknown>
}

export class ProductionAPIService implements KIWissenssystemAPI {
  private baseUrl: string

  constructor(baseUrl: string = 'http://localhost:8080') {
    this.baseUrl = baseUrl
  }

  async sendMessage(message: string): Promise<ChatResponseWithMetadata> {
    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: message,
          context: {},
          use_cache: true
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      // Backend returns QueryResponse with 'response' field, we need 'message'
      // Also include graph metadata for intelligent graph triggering
      return {
        message: result.response || result.answer || 'Keine Antwort erhalten',
        metadata: result.metadata || {}
      }
    } catch (error) {
      console.error('Production API error:', error)
      // Fallback response
      return {
        message: 'Entschuldigung, der Service ist momentan nicht verfügbar. Bitte versuchen Sie es später erneut.',
        metadata: { graph_relevant: false }
      }
    }
  }

  async uploadDocument(formData: FormData): Promise<{ 
    success: boolean; 
    id?: string;
    status?: string;
    task_id?: string;
    filename?: string;
    document_type?: string;
    num_chunks?: number;
    num_controls?: number;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    metadata?: any;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      return {
        success: result.status === 'completed' || result.status === 'processing',
        id: result.task_id || result.document_id,
        status: result.status,
        task_id: result.task_id,
        filename: result.filename,
        document_type: result.document_type,
        num_chunks: result.num_chunks,
        num_controls: result.num_controls,
        metadata: result.metadata
      }
    } catch (error) {
      console.error('Upload API error:', error)
      throw new Error('Upload fehlgeschlagen')
    }
  }

  async analyzeDocumentPreview(formData: FormData): Promise<{
    predicted_document_type: string;
    file_type: string;
    preview_text: string;
    processing_estimate: {
      estimated_duration_seconds: number;
      estimated_chunks: number;
      will_extract_controls: boolean;
      processing_steps: string[];
    };
    confidence_indicators: {
      type_detection: string;
      classification: string;
    };
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/documents/analyze-preview`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Document analysis error:', error)
      throw new Error('Dokument-Analyse fehlgeschlagen')
    }
  }

  async getProcessingStatus(taskId: string): Promise<{
    task_id: string;
    status: string;
    progress: number;
    steps_completed: string[];
    current_step: string;
    estimated_completion: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/documents/processing-status/${taskId}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Processing status error:', error)
      throw new Error('Status konnte nicht abgerufen werden')
    }
  }

  async getKnowledgeGraph(): Promise<{ nodes: GraphNodeData[]; edges: GraphEdgeData[] }> {
    try {
      // Use the new graph data endpoint
      const response = await fetch(`${this.baseUrl}/knowledge-graph/data?limit=100`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      // Transform backend response to frontend format
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const nodes = result.nodes.map((node: any) => ({
        id: node.id,
        label: node.label,
        type: node.type.toLowerCase(),
        size: node.size || 20,
        color: this.getNodeColor(node.type),
        ...node.properties
      }))

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const edges = result.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        type: edge.type.toLowerCase(),
        ...edge.properties
      }))

      console.log(`Loaded ${nodes.length} nodes and ${edges.length} edges from backend`)
      
      return {
        nodes,
        edges
      }
      
    } catch (error) {
      console.error('Graph API error:', error)
      throw new Error('Graph konnte nicht geladen werden')
    }
  }

  private getNodeColor(nodeType: string): string {
    const colorMap: Record<string, string> = {
      'controlitem': '#1976d2',
      'control': '#1976d2',
      'knowledgechunk': '#2e7d32',
      'chunk': '#2e7d32',
      'technology': '#ed6c02',
      'tech': '#ed6c02',
      'entity': '#9c27b0',
      'document': '#d32f2f',
      'concept': '#7b1fa2'
    }
    return colorMap[nodeType.toLowerCase()] || '#757575'
  }

  async getSystemStatus(): Promise<{
    status: 'online' | 'offline' | 'maintenance'
    services: Record<string, boolean>
    performance: {
      responseTime: number
      cpuUsage: number
      memoryUsage: number
      activeConnections: number
    }
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      // Transform backend health response to frontend format
      const isHealthy = result.status === 'healthy'
      
      return {
        status: isHealthy ? 'online' : 'offline',
        services: {
          'API': isHealthy,
          'Database': result.components?.neo4j === 'connected',
          'Vector Store': result.components?.chromadb === 'available',
          'LLM Service': result.components?.query_orchestrator === 'available'
        },
        performance: {
          responseTime: 250, // Mock values since backend doesn't provide this yet
          cpuUsage: 30,
          memoryUsage: 45,
          activeConnections: 8
        }
      }
    } catch (error) {
      console.error('Status API error:', error)
      // Fallback status
      return {
        status: 'offline',
        services: {
          'API': false,
          'Database': false,
          'Vector Store': false,
          'LLM Service': false
        },
        performance: {
          responseTime: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          activeConnections: 0
        }
      }
    }
  }

  // Additional production-specific methods
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        timeout: 5000
      } as RequestInit)
      
      return response.ok
    } catch (error) {
      console.warn('Health check failed:', error)
      return false
    }
  }

  async getAvailableModels(): Promise<string[]> {
    try {
      // This endpoint doesn't exist yet in backend, return default
      return ['gpt-4', 'claude-3', 'gemini-pro']
    } catch (error) {
      console.error('Models API error:', error)
      return []
    }
  }

  // WebSocket connection for real-time features
  createWebSocketConnection(url: string): WebSocket | null {
    try {
      const wsUrl = url.replace('http', 'ws')
      return new WebSocket(`${wsUrl}/ws/chat`)
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      return null
    }
  }
} 