import { useState, useCallback, useRef, useEffect } from 'react'

// === WEBSOCKET RECONNECTION TYPES & CONFIGURATION ===

export interface ReconnectionConfig {
  initialDelay: number          // Initial delay in ms (default: 1000)
  maxDelay: number             // Maximum delay in ms (default: 30000)
  maxAttempts: number          // Maximum retry attempts (default: 10)
  backoffFactor: number        // Exponential backoff factor (default: 2)
  enableJitter: boolean        // Add random jitter to delays (default: true)
  timeoutDuration: number      // Connection timeout in ms (default: 5000)
}

export interface ConnectionStats {
  totalAttempts: number
  successfulConnections: number
  failedConnections: number
  currentAttempt: number
  lastConnectionTime: number | null
  averageConnectionTime: number
  connectionQuality: 'excellent' | 'good' | 'poor' | 'critical'
}

export type ConnectionState = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'failed' | 'reconnecting'

export interface WebSocketHookReturn {
  connectionState: ConnectionState
  connectionStats: ConnectionStats
  isConnected: boolean
  isConnecting: boolean
  hasFailed: boolean
  connect: () => void
  disconnect: () => void
  reconnect: () => void
  send: (data: any) => boolean
  configure: (config: Partial<ReconnectionConfig>) => void
}

// Default configuration
const DEFAULT_CONFIG: ReconnectionConfig = {
  initialDelay: 1000,      // 1 second
  maxDelay: 30000,         // 30 seconds
  maxAttempts: 10,         // 10 attempts
  backoffFactor: 2,        // Double delay each time
  enableJitter: true,      // Random jitter
  timeoutDuration: 5000    // 5 second timeout
}

/**
 * Enhanced WebSocket Hook with Exponential Backoff Reconnection
 * 
 * Features:
 * - Exponential backoff with configurable parameters
 * - Connection quality monitoring
 * - Automatic timeout handling
 * - Jitter to prevent thundering herd
 * - Comprehensive statistics tracking
 * - User-friendly connection state management
 */
export const useWebSocketWithReconnect = (
  url: string,
  options: {
    onMessage?: (event: MessageEvent) => void
    onOpen?: () => void
    onClose?: () => void
    onError?: (error: Event) => void
    config?: Partial<ReconnectionConfig>
    autoConnect?: boolean
  } = {}
): WebSocketHookReturn => {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    config = {},
    autoConnect = true
  } = options

  // State management
  const [connectionState, setConnectionState] = useState<ConnectionState>('idle')
  const [connectionStats, setConnectionStats] = useState<ConnectionStats>({
    totalAttempts: 0,
    successfulConnections: 0,
    failedConnections: 0,
    currentAttempt: 0,
    lastConnectionTime: null,
    averageConnectionTime: 0,
    connectionQuality: 'excellent'
  })

  // Refs for stable references
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const configRef = useRef<ReconnectionConfig>({ ...DEFAULT_CONFIG, ...config })
  const connectionStartTimeRef = useRef<number | null>(null)
  const connectionTimesRef = useRef<number[]>([])

  // === UTILITY FUNCTIONS ===

  /**
   * Calculate delay with exponential backoff and optional jitter
   */
  const calculateDelay = useCallback((attempt: number): number => {
    const baseDelay = Math.min(
      configRef.current.initialDelay * Math.pow(configRef.current.backoffFactor, attempt),
      configRef.current.maxDelay
    )

    if (configRef.current.enableJitter) {
      // Add ±25% jitter to prevent thundering herd
      const jitter = baseDelay * 0.25 * (Math.random() * 2 - 1)
      return Math.max(100, baseDelay + jitter) // Minimum 100ms
    }

    return baseDelay
  }, [])

  /**
   * Update connection statistics
   */
  const updateStats = useCallback((type: 'attempt' | 'success' | 'failure' | 'timeout') => {
    setConnectionStats(prev => {
      const newStats = { ...prev }

      switch (type) {
        case 'attempt':
          newStats.totalAttempts++
          newStats.currentAttempt++
          break

        case 'success':
          newStats.successfulConnections++
          newStats.currentAttempt = 0
          newStats.lastConnectionTime = Date.now()

          // Update connection time statistics
          if (connectionStartTimeRef.current) {
            const connectionTime = Date.now() - connectionStartTimeRef.current
            connectionTimesRef.current.push(connectionTime)
            
            // Keep only last 10 connection times
            if (connectionTimesRef.current.length > 10) {
              connectionTimesRef.current.shift()
            }
            
            newStats.averageConnectionTime = connectionTimesRef.current.reduce((a, b) => a + b, 0) / connectionTimesRef.current.length
          }
          break

        case 'failure':
        case 'timeout':
          newStats.failedConnections++
          break
      }

      // Calculate connection quality
      if (newStats.totalAttempts > 0) {
        const successRate = newStats.successfulConnections / newStats.totalAttempts
        if (successRate >= 0.95) newStats.connectionQuality = 'excellent'
        else if (successRate >= 0.8) newStats.connectionQuality = 'good'
        else if (successRate >= 0.5) newStats.connectionQuality = 'poor'
        else newStats.connectionQuality = 'critical'
      }

      return newStats
    })
  }, [])

  /**
   * Clear all timeouts
   */
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current)
      connectionTimeoutRef.current = null
    }
  }, [])

  /**
   * Clean up WebSocket connection
   */
  const cleanup = useCallback(() => {
    clearTimeouts()
    
    if (wsRef.current) {
      wsRef.current.onopen = null
      wsRef.current.onclose = null
      wsRef.current.onmessage = null
      wsRef.current.onerror = null
      
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
      
      wsRef.current = null
    }
  }, [clearTimeouts])

  // === CONNECTION MANAGEMENT ===

  /**
   * Establish WebSocket connection
   */
  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected')
      return
    }

    cleanup()
    
    setConnectionState('connecting')
    connectionStartTimeRef.current = Date.now()
    updateStats('attempt')

    try {
      wsRef.current = new WebSocket(url)

      // Connection timeout
      connectionTimeoutRef.current = setTimeout(() => {
        console.error('WebSocket connection timeout')
        updateStats('timeout')
        setConnectionState('failed')
        
        if (wsRef.current) {
          wsRef.current.close()
        }
        
        // Trigger reconnection
        scheduleReconnect()
      }, configRef.current.timeoutDuration)

      // Event handlers
      wsRef.current.onopen = () => {
        clearTimeouts()
        console.log('WebSocket connected successfully')
        
        setConnectionState('connected')
        updateStats('success')
        
        if (onOpen) {
          onOpen()
        }
      }

      wsRef.current.onclose = (event) => {
        clearTimeouts()
        console.log('WebSocket disconnected:', event.code, event.reason)
        
        const wasConnected = connectionState === 'connected'
        setConnectionState('disconnected')
        
        if (onClose) {
          onClose()
        }

        // Only attempt reconnection if we were previously connected
        // or if the connection failed unexpectedly
        if (wasConnected || event.code !== 1000) { // 1000 = normal closure
          scheduleReconnect()
        }
      }

      wsRef.current.onmessage = (event) => {
        if (onMessage) {
          onMessage(event)
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        updateStats('failure')
        
        if (onError) {
          onError(error)
        }
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionState('failed')
      updateStats('failure')
      scheduleReconnect()
    }
  }, [url, onMessage, onOpen, onClose, onError, cleanup, updateStats, connectionState])

  /**
   * Schedule reconnection with exponential backoff
   */
  const scheduleReconnect = useCallback(() => {
    const { maxAttempts } = configRef.current
    
    if (connectionStats.currentAttempt >= maxAttempts) {
      console.error(`Max reconnection attempts (${maxAttempts}) reached`)
      setConnectionState('failed')
      return
    }

    const delay = calculateDelay(connectionStats.currentAttempt)
    console.log(`Scheduling reconnection attempt ${connectionStats.currentAttempt + 1} in ${delay}ms`)
    
    setConnectionState('reconnecting')
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, delay)
  }, [connectionStats.currentAttempt, calculateDelay, connect])

  /**
   * Manually disconnect
   */
  const disconnect = useCallback(() => {
    console.log('Manually disconnecting WebSocket')
    clearTimeouts()
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
    }
    
    setConnectionState('disconnected')
  }, [clearTimeouts])

  /**
   * Force reconnection (reset attempt counter)
   */
  const reconnect = useCallback(() => {
    console.log('Force reconnecting WebSocket')
    
    setConnectionStats(prev => ({
      ...prev,
      currentAttempt: 0
    }))
    
    disconnect()
    
    setTimeout(() => {
      connect()
    }, 100)
  }, [disconnect, connect])

  /**
   * Send data through WebSocket
   */
  const send = useCallback((data: any): boolean => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send data')
      return false
    }

    try {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
      return true
    } catch (error) {
      console.error('Failed to send WebSocket data:', error)
      return false
    }
  }, [])

  /**
   * Update configuration
   */
  const configure = useCallback((newConfig: Partial<ReconnectionConfig>) => {
    configRef.current = { ...configRef.current, ...newConfig }
    console.log('WebSocket configuration updated:', newConfig)
  }, [])

  // === EFFECTS ===

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      cleanup()
    }
  }, [autoConnect, connect, cleanup])

  // Computed values
  const isConnected = connectionState === 'connected'
  const isConnecting = connectionState === 'connecting' || connectionState === 'reconnecting'
  const hasFailed = connectionState === 'failed'

  return {
    connectionState,
    connectionStats,
    isConnected,
    isConnecting,
    hasFailed,
    connect,
    disconnect,
    reconnect,
    send,
    configure
  }
} 