import { useCallback } from 'react'
import { useApiError } from './useApiError'
import { getAPIClient } from '@/lib/serviceFactory'

interface GraphNode {
  id: string
  label: string
  type: 'document' | 'concept' | 'entity'
  properties: Record<string, unknown>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
  weight: number
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// Mock fallback data für graceful degradation
const FALLBACK_GRAPH_DATA: GraphData = {
  nodes: [
    { id: '1', label: 'Künstliche Intelligenz', type: 'concept', properties: { description: 'Hauptkonzept der KI' } },
    { id: '2', label: 'Machine Learning', type: 'concept', properties: { description: 'Teilbereich der KI' } },
    { id: '3', label: 'Deep Learning', type: 'concept', properties: { description: 'Teilbereich des ML' } },
    { id: '4', label: 'Neural Networks', type: 'concept', properties: { description: 'Netzwerkarchitektur' } },
    { id: '5', label: 'Computer Vision', type: 'concept', properties: { description: 'Bilderkennung' } },
    { id: '6', label: 'NLP', type: 'concept', properties: { description: 'Sprachverarbeitung' } },
    { id: '7', label: 'Dokument_1.pdf', type: 'document', properties: { path: '/docs/doc1.pdf' } },
    { id: '8', label: 'Dokument_2.pdf', type: 'document', properties: { path: '/docs/doc2.pdf' } },
    { id: '9', label: 'Python', type: 'entity', properties: { type: 'programming_language' } },
    { id: '10', label: 'TensorFlow', type: 'entity', properties: { type: 'framework' } },
  ],
  edges: [
    { id: 'e1', source: '1', target: '2', label: 'enthält', weight: 0.8 },
    { id: 'e2', source: '2', target: '3', label: 'enthält', weight: 0.9 },
    { id: 'e3', source: '3', target: '4', label: 'verwendet', weight: 0.7 },
    { id: 'e4', source: '2', target: '5', label: 'anwendung', weight: 0.6 },
    { id: 'e5', source: '2', target: '6', label: 'anwendung', weight: 0.6 },
    { id: 'e6', source: '7', target: '1', label: 'erwähnt', weight: 0.7 },
    { id: 'e7', source: '8', target: '2', label: 'erwähnt', weight: 0.6 },
    { id: 'e8', source: '9', target: '3', label: 'implementiert', weight: 0.8 },
    { id: 'e9', source: '10', target: '3', label: 'framework', weight: 0.9 },
  ]
}

export function useGraphApi() {
  const {
    executeWithErrorHandling,
    isLoading,
    error,
    clearError,
    canRetry,
    retryCount,
    isRetryableError
  } = useApiError({
    maxRetries: 3,
    retryDelay: 1000,
    onError: (backendError) => {
      console.error('Graph API Error:', backendError)
      // Log with source: 'graph' for debugging
      console.error('Error source: graph, code:', backendError.error_code)
    }
  })

  const loadGraphData = useCallback(async (): Promise<GraphData> => {
    const result = await executeWithErrorHandling(
      async () => {
        try {
          const apiClient = getAPIClient()
          const response = await apiClient.getKnowledgeGraph()
          
          const transformedData: GraphData = {
            nodes: response.nodes.map(node => ({
              id: node.id,
              label: node.label,
              type: (node.type as 'document' | 'concept' | 'entity') || 'concept',
              properties: node.properties
            })),
            edges: response.edges
          }
          
          return transformedData
        } catch (error: unknown) {
          // Erweiterte Error-Behandlung für spezifische Graph-Errors
          const errorMessage = error instanceof Error ? error.message : String(error)
          
          // NEO4J_CONNECTION_FAILED - Non-retryable
          if (errorMessage.includes('NEO4J_CONNECTION_FAILED') || 
              errorMessage.includes('connection') || 
              errorMessage.includes('database')) {
            const graphError = new Error('Graph-Datenbank ist nicht verfügbar. Bitte kontaktieren Sie den Support.')
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            ;(graphError as any).error_code = 'NEO4J_CONNECTION_FAILED'
            throw graphError
          }
          
          // GRAPH_QUERY_TIMEOUT - Retryable
          if (errorMessage.includes('timeout') || 
              errorMessage.includes('GRAPH_QUERY_TIMEOUT')) {
            const graphError = new Error('Graph-Abfrage dauert zu lange. Wird automatisch wiederholt...')
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            ;(graphError as any).error_code = 'GRAPH_QUERY_TIMEOUT'
            throw graphError
          }
          
          // GRAPH_DATA_MALFORMED - Non-retryable mit Fallback
          if (errorMessage.includes('malformed') || 
              errorMessage.includes('parse') ||
              errorMessage.includes('invalid')) {
            console.warn('Graph data malformed, using fallback data')
            return FALLBACK_GRAPH_DATA
          }
          
          // Generic graph error
          const graphError = new Error('Fehler beim Laden des Wissensgraphen. Bitte versuchen Sie es erneut.')
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ;(graphError as any).error_code = 'GRAPH_LOAD_FAILED'
          throw graphError
        }
      },
      { context: 'graph', retryable: true }
    )
    
    return result || FALLBACK_GRAPH_DATA
  }, [executeWithErrorHandling])

  const expandNode = useCallback(async (nodeId: string): Promise<GraphData> => {
    const result = await executeWithErrorHandling(
      async () => {
        try {
          const apiClient = getAPIClient()
          // Simulate node expansion API call
          // In real implementation: await apiClient.expandGraphNode(nodeId)
          console.log(`Expanding node: ${nodeId}`)
          
          // Return incremental graph data
          return {
            nodes: [
              { id: `${nodeId}_child_1`, label: `Child of ${nodeId}`, type: 'concept' as const, properties: { parent: nodeId } }
            ],
            edges: [
              { id: `e_${nodeId}_expand`, source: nodeId, target: `${nodeId}_child_1`, label: 'contains', weight: 0.8 }
            ]
          }
        } catch (error) {
          const expandError = new Error(`Fehler beim Erweitern von Knoten ${nodeId}`)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ;(expandError as any).error_code = 'GRAPH_EXPAND_FAILED'
          throw expandError
        }
      },
      { context: 'graph-expand', retryable: true }
    )
    
    return result || { nodes: [], edges: [] }
  }, [executeWithErrorHandling])

  return {
    loadGraphData,
    expandNode,
    isLoading,
    error,
    clearError,
    canRetry,
    retryCount,
    isRetryableError
  }
} 