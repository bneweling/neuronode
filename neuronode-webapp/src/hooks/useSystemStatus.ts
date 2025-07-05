'use client'

import { useQuery } from '@tanstack/react-query'

import { useApiClient } from '@/contexts/ApiClientContext'
import { SystemStatus, SystemHealth, SystemMetrics } from '@/types/api.generated'

export function useSystemStatus() {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: async (): Promise<SystemStatus> => {
      const response = await apiClient.request<SystemStatus>({
        method: 'GET',
        url: '/health'
      })
      return response
    },
    refetchInterval: 5000, // Automatisches Polling alle 5 Sekunden
    refetchIntervalInBackground: true, // Polling auch im Hintergrund
    staleTime: 0, // Immer als "stale" behandeln für Live-Updates
    gcTime: 30000, // 30 Sekunden Cache-Zeit
    retry: 3, // Bis zu 3 Retries bei Fehlern
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  })
}

export function useSystemMetrics() {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['system', 'metrics'],
    queryFn: async (): Promise<SystemMetrics> => {
      const response = await apiClient.request<SystemMetrics>({
        method: 'GET',
        url: '/system/metrics'
      })
      return response
    },
    refetchInterval: 10000, // Alle 10 Sekunden
    refetchIntervalInBackground: true,
    staleTime: 0,
    gcTime: 60000, // 1 Minute Cache
  })
}

export function useSystemHealth() {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['system', 'health'],
    queryFn: async (): Promise<SystemHealth> => {
      const response = await apiClient.request<SystemHealth>({
        method: 'GET',
        url: '/system/health'
      })
      return response
    },
    refetchInterval: 15000, // Alle 15 Sekunden
    refetchIntervalInBackground: true,
    staleTime: 0,
    gcTime: 60000, // 1 Minute Cache
  })
} 