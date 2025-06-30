/**
 * React Hook for App Configuration Management
 * Provides reactive access to demo/production mode switching
 */

import { useState, useEffect, useCallback } from 'react'

import { configManager, type AppConfig, type AppMode } from '@/config/environment'

export interface UseAppConfigReturn {
  config: AppConfig
  mode: AppMode
  isDemo: boolean
  isProduction: boolean
  isHealthy: boolean
  isLoading: boolean
  switchMode: (mode: AppMode) => void
  updateProductionUrls: (apiUrl: string) => void
  checkHealth: () => Promise<boolean>
  reset: () => void
}

export function useAppConfig(): UseAppConfigReturn {
  const [config, setConfig] = useState<AppConfig>(configManager.getConfig())
  const [isHealthy, setIsHealthy] = useState<boolean>(true)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  // Subscribe to config changes
  useEffect(() => {
    const unsubscribe = configManager.subscribe((newConfig) => {
      setConfig(newConfig)
    })

    return unsubscribe
  }, [])

  const checkHealthStatus = useCallback(async () => {
    if (config.mode === 'demo') {
      setIsHealthy(true)
      return
    }

    setIsLoading(true)
    try {
      const healthy = await configManager.checkHealth()
      setIsHealthy(healthy)
    } catch (error) {
      console.error('Health check failed:', error)
      setIsHealthy(false)
    } finally {
      setIsLoading(false)
    }
  }, [config.mode])

  // Health check on mount and mode change
  useEffect(() => {
    if (config.mode === 'production') {
      checkHealthStatus()
    } else {
      setIsHealthy(true)
    }
  }, [config.mode, config.apiUrl, checkHealthStatus])

  const switchMode = useCallback((mode: AppMode) => {
    setIsLoading(true)
    configManager.switchMode(mode)
    // Loading state will be cleared by health check effect
  }, [])

  const updateProductionUrls = useCallback((apiUrl: string) => {
    configManager.updateProductionUrls(apiUrl)
  }, [])

  const checkHealth = useCallback(async (): Promise<boolean> => {
    await checkHealthStatus()
    return isHealthy
  }, [checkHealthStatus, isHealthy])

  const reset = useCallback(() => {
    configManager.reset()
  }, [])

  return {
    config,
    mode: config.mode,
    isDemo: config.mode === 'demo',
    isProduction: config.mode === 'production',
    isHealthy,
    isLoading,
    switchMode,
    updateProductionUrls,
    checkHealth,
    reset
  }
}

// Specialized hooks for specific use cases
export function useApiUrl(): string {
  const { config } = useAppConfig()
  return config.apiUrl
}

export function useWebSocketUrl(): string {
  return configManager.getWebSocketUrl()
}

export function useEndpointUrl(endpoint: keyof AppConfig['endpoints']): string {
  return configManager.getEndpointUrl(endpoint)
}

export function useFeatures() {
  const { config } = useAppConfig()
  return config.features
}

export function useModeIndicator() {
  const { mode, isHealthy, isLoading } = useAppConfig()
  
  return {
    mode,
    label: mode === 'demo' ? 'Demo Modus' : 'Produktions Modus',
    color: mode === 'demo' ? 'warning' : (isHealthy ? 'success' : 'error'),
    icon: mode === 'demo' ? 'science' : (isHealthy ? 'cloud' : 'cloud_off'),
    isLoading
  }
} 