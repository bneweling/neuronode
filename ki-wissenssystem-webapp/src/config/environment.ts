/**
 * Environment Configuration & Mode Management
 * Handles switching between Demo and Production modes
 */

export type AppMode = 'demo' | 'production'

export interface AppConfig {
  mode: AppMode
  apiUrl: string
  wsUrl: string
  features: {
    mockData: boolean
    realTimeChat: boolean
    fileUpload: boolean
    graphVisualization: boolean
  }
  endpoints: {
    chat: string
    upload: string
    graph: string
    status: string
    websocket: string
  }
}

export interface ProductionConfig {
  apiUrl: string
  wsUrl: string
  healthCheckInterval: number
  retryAttempts: number
  timeout: number
}

// Default configurations
const DEMO_CONFIG: AppConfig = {
  mode: 'demo',
  apiUrl: 'http://localhost:3000', // Frontend selbst für Mock-Daten
  wsUrl: 'ws://localhost:3000/mock-ws',
  features: {
    mockData: true,
    realTimeChat: true, // Simuliert
    fileUpload: true, // Simuliert
    graphVisualization: true
  },
  endpoints: {
    chat: '/api/mock/chat',
    upload: '/api/mock/upload',
    graph: '/api/mock/graph',
    status: '/api/mock/status',
    websocket: '/mock-ws/chat'
  }
}

const PRODUCTION_CONFIG: AppConfig = {
  mode: 'production',
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  features: {
    mockData: false,
    realTimeChat: true,
    fileUpload: true,
    graphVisualization: true
  },
  endpoints: {
    chat: '/query', // Backend verwendet /query statt /api/chat
    upload: '/documents/upload',
    graph: '/knowledge-graph/stats', // Backend verwendet anderen Endpoint
    status: '/health', // Backend verwendet /health statt /api/system/status
    websocket: '/ws/chat'
  }
}

// Environment Detection
export function detectEnvironment(): AppMode {
  if (typeof window === 'undefined') return 'demo' // SSR fallback
  
  // Check localStorage for user preference
  const savedMode = localStorage.getItem('ki-app-mode') as AppMode
  if (savedMode && ['demo', 'production'].includes(savedMode)) {
    return savedMode
  }
  
  // Auto-detect based on environment
  if (process.env.NODE_ENV === 'development') {
    return 'demo'
  }
  
  return 'production'
}

// Configuration Manager
export class ConfigManager {
  private static instance: ConfigManager
  private currentConfig: AppConfig
  private listeners: Set<(config: AppConfig) => void> = new Set()

  private constructor() {
    const mode = detectEnvironment()
    this.currentConfig = mode === 'demo' ? { ...DEMO_CONFIG } : { ...PRODUCTION_CONFIG }
  }

  static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager()
    }
    return ConfigManager.instance
  }

  getConfig(): AppConfig {
    return { ...this.currentConfig }
  }

  getMode(): AppMode {
    return this.currentConfig.mode
  }

  isDemo(): boolean {
    return this.currentConfig.mode === 'demo'
  }

  isProduction(): boolean {
    return this.currentConfig.mode === 'production'
  }

  switchMode(mode: AppMode): void {
    const newConfig = mode === 'demo' ? { ...DEMO_CONFIG } : { ...PRODUCTION_CONFIG }
    
    // Apply any custom overrides
    const customApiUrl = localStorage.getItem('ki-custom-api-url')
    if (customApiUrl && mode === 'production') {
      newConfig.apiUrl = customApiUrl
      newConfig.wsUrl = customApiUrl.replace('http', 'ws')
    }

    this.currentConfig = newConfig
    
    // Persist user choice
    localStorage.setItem('ki-app-mode', mode)
    
    // Notify listeners
    this.listeners.forEach(listener => listener(newConfig))
    
    console.log(`🔄 Switched to ${mode} mode`, newConfig)
  }

  updateProductionUrls(apiUrl: string): void {
    if (this.currentConfig.mode === 'production') {
      this.currentConfig.apiUrl = apiUrl
      this.currentConfig.wsUrl = apiUrl.replace('http', 'ws')
    }
    
    // Persist custom URL
    localStorage.setItem('ki-custom-api-url', apiUrl)
    
    // Notify listeners
    this.listeners.forEach(listener => listener(this.currentConfig))
  }

  subscribe(listener: (config: AppConfig) => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  // Health check for production mode
  async checkHealth(): Promise<boolean> {
    if (this.currentConfig.mode === 'demo') return true
    
    try {
      const response = await fetch(`${this.currentConfig.apiUrl}/health`, {
        method: 'GET',
        timeout: 5000
      } as RequestInit)
      
      return response.ok
    } catch (error) {
      console.warn('Health check failed:', error)
      return false
    }
  }

  // Get full endpoint URL
  getEndpointUrl(endpoint: keyof AppConfig['endpoints']): string {
    return `${this.currentConfig.apiUrl}${this.currentConfig.endpoints[endpoint]}`
  }

  // Get WebSocket URL
  getWebSocketUrl(): string {
    return `${this.currentConfig.wsUrl}${this.currentConfig.endpoints.websocket}`
  }

  // Reset to defaults
  reset(): void {
    localStorage.removeItem('ki-app-mode')
    localStorage.removeItem('ki-custom-api-url')
    
    const mode = detectEnvironment()
    this.switchMode(mode)
  }
}

// Singleton instance
export const configManager = ConfigManager.getInstance()

// React Hook (to be created separately)
export { useAppConfig } from '@/hooks/useAppConfig'

// Utility functions
export function getApiUrl(): string {
  return configManager.getConfig().apiUrl
}

export function getWebSocketUrl(): string {
  return configManager.getWebSocketUrl()
}

export function isDemo(): boolean {
  return configManager.isDemo()
}

export function isProduction(): boolean {
  return configManager.isProduction()
} 