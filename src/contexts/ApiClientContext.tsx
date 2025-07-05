'use client'

import { createContext, useContext, ReactNode } from 'react'

// === API ERROR TYPES ===
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(message: string, public originalError?: Error) {
    super(message)
    this.name = 'NetworkError'
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message)
    this.name = 'TimeoutError'
  }
}

// === CIRCUIT BREAKER IMPLEMENTATION ===
class CircuitBreaker {
  private failures = 0
  private lastFailureTime = 0
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED'

  constructor(
    private threshold: number = 5,
    private timeout: number = 60000 // 1 minute
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN'
      } else {
        throw new ApiError('Circuit breaker is OPEN - service temporarily unavailable')
      }
    }

    try {
      const result = await operation()
      this.onSuccess()
      return result
    } catch (error) {
      this.onFailure()
      throw error
    }
  }

  private onSuccess() {
    this.failures = 0
    this.state = 'CLOSED'
  }

  private onFailure() {
    this.failures++
    this.lastFailureTime = Date.now()
    
    if (this.failures >= this.threshold) {
      this.state = 'OPEN'
    }
  }

  getState() {
    return {
      state: this.state,
      failures: this.failures,
      lastFailureTime: this.lastFailureTime
    }
  }
}

// === RETRY CONFIGURATION ===
interface RetryConfig {
  maxRetries: number
  baseDelay: number
  maxDelay: number
  backoffMultiplier: number
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2
}

// === ENHANCED API CLIENT ===
export class ApiClient {
  private baseURL: string
  private timeout: number
  private circuitBreaker: CircuitBreaker
  private retryConfig: RetryConfig

  constructor(config: { 
    baseURL: string
    timeout?: number
    circuitBreakerThreshold?: number
    circuitBreakerTimeout?: number
    retryConfig?: Partial<RetryConfig>
  }) {
    this.baseURL = config.baseURL.replace(/\/+$/, '')
    this.timeout = config.timeout || 10000
    this.circuitBreaker = new CircuitBreaker(
      config.circuitBreakerThreshold || 5,
      config.circuitBreakerTimeout || 60000
    )
    this.retryConfig = { ...defaultRetryConfig, ...config.retryConfig }
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private calculateRetryDelay(attempt: number): number {
    const delay = this.retryConfig.baseDelay * Math.pow(this.retryConfig.backoffMultiplier, attempt)
    return Math.min(delay, this.retryConfig.maxDelay)
  }

  private shouldRetry(error: Error, attempt: number): boolean {
    if (attempt >= this.retryConfig.maxRetries) {
      return false
    }

    // Don't retry on client errors (4xx)
    if (error instanceof ApiError && error.status && error.status >= 400 && error.status < 500) {
      return false
    }

    // Retry on network errors, timeouts, and server errors (5xx)
    return (
      error instanceof NetworkError ||
      error instanceof TimeoutError ||
      (error instanceof ApiError && error.status && error.status >= 500)
    )
  }

  private createDetailedError(error: unknown, url: string, method: string): Error {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return new TimeoutError(`Request to ${method} ${url} timed out after ${this.timeout}ms`)
      }
      
      if (error.message.includes('fetch')) {
        return new NetworkError(
          `Network error while calling ${method} ${url}: ${error.message}`,
          error
        )
      }
      
      return error
    }
    
    return new ApiError(`Unknown error occurred while calling ${method} ${url}`)
  }

  private async executeWithRetry<T>(operation: () => Promise<T>, context: string): Promise<T> {
    let lastError: Error

    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        return await this.circuitBreaker.execute(operation)
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        
        if (!this.shouldRetry(lastError, attempt)) {
          break
        }

        if (attempt < this.retryConfig.maxRetries) {
          const delay = this.calculateRetryDelay(attempt)
          console.warn(`${context} failed (attempt ${attempt + 1}), retrying in ${delay}ms:`, lastError.message)
          await this.delay(delay)
        }
      }
    }

    throw lastError!
  }

  async request<T>(config: {
    method: 'GET' | 'POST' | 'PUT' | 'DELETE'
    url: string
    data?: unknown
    headers?: Record<string, string>
    timeout?: number
    skipRetry?: boolean
  }): Promise<T> {
    const operation = async (): Promise<T> => {
      const controller = new AbortController()
      const requestTimeout = config.timeout || this.timeout
      const timeoutId = setTimeout(() => controller.abort(), requestTimeout)

      try {
        const url = config.url.startsWith('http') ? config.url : `${this.baseURL}${config.url}`
        
        const requestConfig: RequestInit = {
          method: config.method,
          headers: {
            'Content-Type': 'application/json',
            ...config.headers,
          },
          signal: controller.signal,
        }

        if (config.data && config.method !== 'GET') {
          if (config.data instanceof FormData) {
            // For FormData, remove Content-Type to let browser set it
            delete requestConfig.headers!['Content-Type']
            requestConfig.body = config.data
          } else {
            requestConfig.body = JSON.stringify(config.data)
          }
        }

        const response = await fetch(url, requestConfig)
        clearTimeout(timeoutId)

        if (!response.ok) {
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`
          let errorDetails: unknown

          try {
            const errorData = await response.json()
            errorMessage = errorData.message || errorData.detail || errorMessage
            errorDetails = errorData
          } catch {
            // If response is not JSON, use default message
          }

          throw new ApiError(
            errorMessage,
            response.status,
            response.status.toString(),
            errorDetails
          )
        }

        // Handle different content types
        const contentType = response.headers.get('content-type')
        if (contentType?.includes('application/json')) {
          return await response.json()
        } else if (contentType?.includes('text/')) {
          return await response.text() as unknown as T
        } else {
          return await response.blob() as unknown as T
        }
      } catch (error) {
        clearTimeout(timeoutId)
        throw this.createDetailedError(error, config.url, config.method)
      }
    }

    const context = `${config.method} ${config.url}`
    
    if (config.skipRetry) {
      return await operation()
    } else {
      return await this.executeWithRetry(operation, context)
    }
  }

  // === CONVENIENCE METHODS ===
  async get<T>(url: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>({ method: 'GET', url, headers })
  }

  async post<T>(url: string, data?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>({ method: 'POST', url, data, headers })
  }

  async put<T>(url: string, data?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data, headers })
  }

  async delete<T>(url: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>({ method: 'DELETE', url, headers })
  }

  // === HEALTH CHECK METHODS ===
  async healthCheck(): Promise<boolean> {
    try {
      await this.request({
        method: 'GET',
        url: '/health',
        timeout: 5000,
        skipRetry: true
      })
      return true
    } catch {
      return false
    }
  }

  getCircuitBreakerState() {
    return this.circuitBreaker.getState()
  }

  // === SPECIFIC API METHODS ===
  async sendMessage(message: string): Promise<import('@/types/api.generated').ChatResponse> {
    return this.post('/query', { query: message })
  }

  async getSystemStatus(): Promise<import('@/types/api.generated').SystemStatus> {
    return this.get('/health')
  }

  async uploadDocument(file: File): Promise<import('@/types/api.generated').DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.request({
      method: 'POST',
      url: '/documents/upload',
      data: formData,
      timeout: 30000 // Longer timeout for file uploads
    })
  }

  async getGraphData(): Promise<import('@/types/api.generated').GraphData> {
    return this.get('/knowledge-graph/data')
  }
}

// === CONTEXT IMPLEMENTATION ===
const ApiClientContext = createContext<ApiClient | null>(null)

interface ApiClientProviderProps {
  children: ReactNode
  config?: {
    baseURL?: string
    timeout?: number
    circuitBreakerThreshold?: number
    circuitBreakerTimeout?: number
    retryConfig?: Partial<RetryConfig>
  }
}

export function ApiClientProvider({ 
  children, 
  config 
}: ApiClientProviderProps) {
  const apiClient = new ApiClient({
    baseURL: config?.baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
    timeout: config?.timeout || 10000,
    circuitBreakerThreshold: config?.circuitBreakerThreshold || 5,
    circuitBreakerTimeout: config?.circuitBreakerTimeout || 60000,
    retryConfig: config?.retryConfig
  })

  return (
    <ApiClientContext.Provider value={apiClient}>
      {children}
    </ApiClientContext.Provider>
  )
}

export function useApiClient(): ApiClient {
  const client = useContext(ApiClientContext)
  if (!client) {
    throw new Error('useApiClient must be used within ApiClientProvider')
  }
  return client
} 