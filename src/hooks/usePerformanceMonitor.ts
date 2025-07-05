import { useState, useEffect, useCallback } from 'react'

interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  networkLatency: number
  apiResponseTime: number
  componentCount: number
  rerenderCount: number
  errorCount: number
}

interface PerformanceThresholds {
  renderTime: number
  memoryUsage: number
  networkLatency: number
  apiResponseTime: number
}

interface PerformanceAlert {
  id: string
  type: 'warning' | 'error' | 'critical'
  message: string
  metric: keyof PerformanceMetrics
  value: number
  threshold: number
  timestamp: number
}

interface UsePerformanceMonitorOptions {
  enabled?: boolean
  thresholds?: Partial<PerformanceThresholds>
  sampleRate?: number
  onAlert?: (alert: PerformanceAlert) => void
}

const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  renderTime: 16, // 16ms for 60fps
  memoryUsage: 50, // 50MB
  networkLatency: 1000, // 1 second
  apiResponseTime: 2000, // 2 seconds
}

export function usePerformanceMonitor(options: UsePerformanceMonitorOptions = {}) {
  const {
    enabled = true,
    thresholds = DEFAULT_THRESHOLDS,
    sampleRate = 1000, // Sample every 1 second
    onAlert
  } = options

  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    memoryUsage: 0,
    networkLatency: 0,
    apiResponseTime: 0,
    componentCount: 0,
    rerenderCount: 0,
    errorCount: 0
  })

  const [alerts, setAlerts] = useState<PerformanceAlert[]>([])
  const [isMonitoring, setIsMonitoring] = useState(false)

  const mergedThresholds = { ...DEFAULT_THRESHOLDS, ...thresholds }

  // Create performance alert
  const createAlert = useCallback((
    type: PerformanceAlert['type'],
    message: string,
    metric: keyof PerformanceMetrics,
    value: number,
    threshold: number
  ) => {
    const alert: PerformanceAlert = {
      id: `${Date.now()}-${Math.random()}`,
      type,
      message,
      metric,
      value,
      threshold,
      timestamp: Date.now()
    }

    setAlerts(prev => [...prev.slice(-9), alert]) // Keep last 10 alerts
    
    if (onAlert) {
      onAlert(alert)
    }
  }, [onAlert])

  // Measure render time
  const measureRenderTime = useCallback(() => {
    const start = performance.now()
    return () => {
      const end = performance.now()
      const renderTime = end - start
      
      setMetrics(prev => ({
        ...prev,
        renderTime,
        rerenderCount: prev.rerenderCount + 1
      }))

      if (renderTime > mergedThresholds.renderTime) {
        createAlert('warning', 'Slow render detected', 'renderTime', renderTime, mergedThresholds.renderTime)
      }
    }
  }, [mergedThresholds.renderTime, createAlert])

  // Measure memory usage
  const measureMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      const memoryUsage = memory.usedJSHeapSize / 1024 / 1024 // Convert to MB
      
      setMetrics(prev => ({
        ...prev,
        memoryUsage
      }))

      if (memoryUsage > mergedThresholds.memoryUsage) {
        createAlert('warning', 'High memory usage detected', 'memoryUsage', memoryUsage, mergedThresholds.memoryUsage)
      }
    }
  }, [mergedThresholds.memoryUsage, createAlert])

  // Measure network latency
  const measureNetworkLatency = useCallback(async () => {
    try {
      const start = performance.now()
      await fetch('/api/health', { 
        method: 'HEAD',
        cache: 'no-cache'
      })
      const end = performance.now()
      const networkLatency = end - start
      
      setMetrics(prev => ({
        ...prev,
        networkLatency
      }))

      if (networkLatency > mergedThresholds.networkLatency) {
        createAlert('warning', 'High network latency detected', 'networkLatency', networkLatency, mergedThresholds.networkLatency)
      }
    } catch (error) {
      // Network error - set high latency
      setMetrics(prev => ({
        ...prev,
        networkLatency: mergedThresholds.networkLatency * 2,
        errorCount: prev.errorCount + 1
      }))
      
      createAlert('error', 'Network connectivity issue', 'networkLatency', mergedThresholds.networkLatency * 2, mergedThresholds.networkLatency)
    }
  }, [mergedThresholds.networkLatency, createAlert])

  // Measure API response time
  const measureApiResponseTime = useCallback((url: string) => {
    const start = performance.now()
    
    return () => {
      const end = performance.now()
      const apiResponseTime = end - start
      
      setMetrics(prev => ({
        ...prev,
        apiResponseTime
      }))

      if (apiResponseTime > mergedThresholds.apiResponseTime) {
        createAlert('warning', `Slow API response from ${url}`, 'apiResponseTime', apiResponseTime, mergedThresholds.apiResponseTime)
      }
    }
  }, [mergedThresholds.apiResponseTime, createAlert])

  // Start monitoring
  const startMonitoring = useCallback(() => {
    if (!enabled) return

    setIsMonitoring(true)
    
    const interval = setInterval(() => {
      measureMemoryUsage()
      measureNetworkLatency()
    }, sampleRate)

    return () => {
      clearInterval(interval)
      setIsMonitoring(false)
    }
  }, [enabled, sampleRate, measureMemoryUsage, measureNetworkLatency])

  // Stop monitoring
  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false)
  }, [])

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  // Get performance score (0-100)
  const getPerformanceScore = useCallback(() => {
    const scores = [
      Math.max(0, 100 - (metrics.renderTime / mergedThresholds.renderTime) * 100),
      Math.max(0, 100 - (metrics.memoryUsage / mergedThresholds.memoryUsage) * 100),
      Math.max(0, 100 - (metrics.networkLatency / mergedThresholds.networkLatency) * 100),
      Math.max(0, 100 - (metrics.apiResponseTime / mergedThresholds.apiResponseTime) * 100)
    ]
    
    return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
  }, [metrics, mergedThresholds])

  // Track component performance (to be used in useEffect)
  const trackComponentPerformance = useCallback((componentName: string) => {
    const endMeasure = measureRenderTime()
    
    return () => {
      endMeasure()
    }
  }, [measureRenderTime])

  // Get performance summary
  const getPerformanceSummary = useCallback(() => {
    const recentAlerts = alerts.slice(-5)
    const criticalAlerts = alerts.filter(alert => alert.type === 'critical')
    
    return {
      ...metrics,
      totalAlerts: alerts.length,
      recentAlerts,
      criticalAlerts: criticalAlerts.length,
      isHealthy: criticalAlerts.length === 0 && metrics.renderTime < mergedThresholds.renderTime
    }
  }, [metrics, alerts, mergedThresholds.renderTime])

  // Effect to start monitoring
  useEffect(() => {
    if (!enabled) return

    const cleanup = startMonitoring()
    return cleanup
  }, [enabled, startMonitoring])

  return {
    metrics,
    alerts,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    clearAlerts,
    measureRenderTime,
    measureApiResponseTime,
    trackComponentPerformance,
    getPerformanceScore,
    getPerformanceSummary,
    thresholds: mergedThresholds
  }
}

export default usePerformanceMonitor 