import { useMemo } from 'react'

import { useGraphData, useGraphStats } from './useGraphApi'

// Re-exporting for easy access in components
export { useGraphData, useGraphStats }

// Simplified state hook that wraps TanStack Query hooks
export const useGraphState = () => {
  const graphDataQuery = useGraphData()
  const graphStatsQuery = useGraphStats()

  const isLoading = useMemo(
    () => graphDataQuery.isLoading || graphStatsQuery.isLoading,
    [graphDataQuery.isLoading, graphStatsQuery.isLoading]
  )

  const error = useMemo(
    () => graphDataQuery.error || graphStatsQuery.error,
    [graphDataQuery.error, graphStatsQuery.error]
  )

  return {
    graphData: graphDataQuery.data,
    graphStats: graphStatsQuery.data,
    isLoading,
    error,
    isError: graphDataQuery.isError || graphStatsQuery.isError,
    refetchGraphData: graphDataQuery.refetch,
    refetchGraphStats: graphStatsQuery.refetch,
  }
} 