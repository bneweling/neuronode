'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

interface PerformanceMetrics {
  componentRenders: Map<string, number>
  apiCalls: Map<string, { count: number; averageTime: number; totalTime: number }>
  userInteractions: Map<string, number>
  memoryUsage: number
  renderTimes: Map<string, number[]>
}

interface ApiCallMetric {
  endpoint: string
  method: string
  duration: number
  status: 'success' | 'error'
  timestamp: number
}

interface UserInteractionMetric {
  action: string
  data?: Record<string, any>
  timestamp: number
}

interface PerformanceAlert {
  type: 'slow_render' | 'memory_high' | 'api_slow' | 'error_rate_high'
  message: string
  timestamp: number
  data?: Record<string, any>
}

export function usePerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    componentRenders: new Map(),
    apiCalls: new Map(),
    userInteractions: new Map(),
    memoryUsage: 0,
    renderTimes: new Map(),
  })
  
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([])
  const alertsRef = useRef<PerformanceAlert[]>([])
  const metricsRef = useRef<PerformanceMetrics>(metrics)
  
  // Update refs when state changes
  useEffect(() => {
    metricsRef.current = metrics
  }, [metrics])
  
  useEffect(() => {
    alertsRef.current = alerts
  }, [alerts])

  // Memory monitoring
  useEffect(() => {
    const updateMemoryUsage = () => {
      if ('memory' in performance) {
        const memInfo = (performance as any).memory
        const memoryUsage = memInfo.usedJSHeapSize / (1024 * 1024) // MB
        
        setMetrics(prev => ({
          ...prev,
          memoryUsage
        }))
        
        // Alert if memory usage is high (>100MB)
        if (memoryUsage > 100) {
          addAlert({
            type: 'memory_high',
            message: `High memory usage detected: ${memoryUsage.toFixed(1)}MB`,
            timestamp: Date.now(),
            data: { memoryUsage }
          })
        }
      }
    }
    
    const interval = setInterval(updateMemoryUsage, 10000) // Check every 10 seconds
    updateMemoryUsage() // Initial check
    
    return () => clearInterval(interval)
  }, [])

  const addAlert = useCallback((alert: PerformanceAlert) => {
    setAlerts(prev => {
      const newAlerts = [...prev, alert]
      // Keep only last 10 alerts
      return newAlerts.slice(-10)
    })
  }, [])

  // Track component performance
  const trackComponentPerformance = useCallback((componentName: string, phase: 'render' | 'mount' | 'update') => {
    const startTime = performance.now()
    
    return () => {
      const endTime = performance.now()
      const duration = endTime - startTime
      
      setMetrics(prev => {
        const newMetrics = { ...prev }
        
        // Update render count
        const currentCount = newMetrics.componentRenders.get(componentName) || 0
        newMetrics.componentRenders.set(componentName, currentCount + 1)
        
        // Update render times
        const currentTimes = newMetrics.renderTimes.get(componentName) || []
        currentTimes.push(duration)
        // Keep only last 100 renders
        if (currentTimes.length > 100) {
          currentTimes.shift()
        }
        newMetrics.renderTimes.set(componentName, currentTimes)
        
        return newMetrics
      })
      
      // Alert if render is slow (>100ms)
      if (duration > 100) {
        addAlert({
          type: 'slow_render',
          message: `Slow ${phase} detected in ${componentName}: ${duration.toFixed(2)}ms`,
          timestamp: Date.now(),
          data: { componentName, phase, duration }
        })
      }
    }
  }, [addAlert])

  // Track API call performance
  const trackApiCall = useCallback((endpoint: string, method: string, duration: number, status: 'success' | 'error') => {
    const metric: ApiCallMetric = {
      endpoint,
      method,
      duration,
      status,
      timestamp: Date.now()
    }
    
    setMetrics(prev => {
      const newMetrics = { ...prev }
      const key = `${method} ${endpoint}`
      const existing = newMetrics.apiCalls.get(key) || { count: 0, averageTime: 0, totalTime: 0 }
      
      const newCount = existing.count + 1
      const newTotalTime = existing.totalTime + duration
      const newAverageTime = newTotalTime / newCount
      
      newMetrics.apiCalls.set(key, {
        count: newCount,
        averageTime: newAverageTime,
        totalTime: newTotalTime
      })
      
      return newMetrics
    })
    
    // Alert if API call is slow (>5000ms)
    if (duration > 5000) {
      addAlert({
        type: 'api_slow',
        message: `Slow API call detected: ${method} ${endpoint} took ${duration.toFixed(2)}ms`,
        timestamp: Date.now(),
        data: { endpoint, method, duration, status }
      })
    }
    
    // Track error rate
    if (status === 'error') {
      setTimeout(() => {
        const key = `${method} ${endpoint}`
        const apiMetric = metricsRef.current.apiCalls.get(key)
        if (apiMetric && apiMetric.count >= 10) {
          // Check error rate of last 10 calls (simplified)
          const errorRate = 0.3 // This would need more sophisticated tracking
          if (errorRate > 0.3) {
            addAlert({
              type: 'error_rate_high',
              message: `High error rate detected for ${method} ${endpoint}: ${(errorRate * 100).toFixed(1)}%`,
              timestamp: Date.now(),
              data: { endpoint, method, errorRate }
            })
          }
        }
      }, 100)
    }
  }, [addAlert])

  // Track user interactions
  const trackUserInteraction = useCallback((action: string, data?: Record<string, any>) => {
    const metric: UserInteractionMetric = {
      action,
      data,
      timestamp: Date.now()
    }
    
    setMetrics(prev => {
      const newMetrics = { ...prev }
      const currentCount = newMetrics.userInteractions.get(action) || 0
      newMetrics.userInteractions.set(action, currentCount + 1)
      return newMetrics
    })
  }, [])

  // Clear old alerts
  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  // Get performance summary
  const getPerformanceSummary = useCallback(() => {
    const summary = {
      totalComponents: metrics.componentRenders.size,
      totalApiCalls: Array.from(metrics.apiCalls.values()).reduce((sum, metric) => sum + metric.count, 0),
      totalUserInteractions: Array.from(metrics.userInteractions.values()).reduce((sum, count) => sum + count, 0),
      memoryUsage: metrics.memoryUsage,
      averageRenderTime: 0,
      slowestComponent: '',
      slowestApi: '',
      activeAlerts: alerts.length
    }
    
    // Calculate average render time
    const renderTimes = Array.from(metrics.renderTimes.values()).flat()
    if (renderTimes.length > 0) {
      summary.averageRenderTime = renderTimes.reduce((sum, time) => sum + time, 0) / renderTimes.length
    }
    
    // Find slowest component
    let slowestTime = 0
    metrics.renderTimes.forEach((times, component) => {
      const avgTime = times.reduce((sum, time) => sum + time, 0) / times.length
      if (avgTime > slowestTime) {
        slowestTime = avgTime
        summary.slowestComponent = component
      }
    })
    
    // Find slowest API
    let slowestApiTime = 0
    metrics.apiCalls.forEach((metric, key) => {
      if (metric.averageTime > slowestApiTime) {
        slowestApiTime = metric.averageTime
        summary.slowestApi = key
      }
    })
    
    return summary
  }, [metrics, alerts])

  return {
    metrics,
    alerts,
    trackComponentPerformance,
    trackApiCall,
    trackUserInteraction,
    clearAlerts,
    getPerformanceSummary,
  }
} 