import { useQuery } from '@tanstack/react-query'

import { useApiClient } from '@/contexts/ApiClientContext'

// Define GraphData and GraphStats types since they don't exist in the generated API
export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphNode {
  id: string
  label: string
  type: 'document' | 'concept' | 'entity'
  properties: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
  weight: number
}

export interface GraphStats {
  totalNodes: number
  totalEdges: number
  documentNodes: number
  conceptNodes: number
  entityNodes: number
  relationshipTypes: string[]
}

type GraphDataResponse = { data: GraphData }
type GraphStatsResponse = GraphStats

export const useGraphData = () => {
  const apiClient = useApiClient()

  return useQuery<GraphData, Error>({
    queryKey: ['graphData'],
    queryFn: async () => {
      const response = await apiClient.get<GraphDataResponse>('/knowledge-graph/data')
      return response.data || { nodes: [], edges: [] }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
  })
}

export const useGraphStats = () => {
  const apiClient = useApiClient()

  return useQuery<GraphStats, Error>({
    queryKey: ['graphStats'],
    queryFn: async () => {
      const response = await apiClient.get<GraphStatsResponse>('/knowledge-graph/stats')
      return response || {
        totalNodes: 0,
        totalEdges: 0,
        documentNodes: 0,
        conceptNodes: 0,
        entityNodes: 0,
        relationshipTypes: []
      }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}
