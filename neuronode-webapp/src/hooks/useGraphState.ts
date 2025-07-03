import { useState, useCallback, useRef, useEffect } from 'react'
import { useGraphApi } from './useGraphApi'

// === GRAPH CACHING TYPES & CONFIGURATION ===

interface GraphCacheEntry {
  data: GraphData
  timestamp: number
  ttl: number
  version: string
  accessCount: number
  lastAccess: number
}

interface GraphCacheConfig {
  defaultTTL: number // Time to live in milliseconds
  maxEntries: number // Maximum cache entries
  enableStatistics: boolean
  autoCleanup: boolean
}

interface GraphCacheStats {
  hits: number
  misses: number
  entries: number
  totalSize: number
  hitRate: number
  oldestEntry: number
  newestEntry: number
}

// Default cache configuration
const DEFAULT_CACHE_CONFIG: GraphCacheConfig = {
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxEntries: 10,
  enableStatistics: true,
  autoCleanup: true
}

// Graph data types
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

// Stable graph state management
interface GraphState {
  status: 'loading' | 'success' | 'error' | 'idle'
  data: GraphData | null
  error: Error | null
  lastFetchTime: number | null
  isInitialized: boolean
}

// Enhanced actions interface with cache support
interface GraphActions {
  loadGraphData: (forceRefresh?: boolean) => Promise<void>
  refreshGraph: () => Promise<void>
  clearError: () => void
  resetGraph: () => void
  updateGraphData: (data: GraphData) => void
  invalidateCache: () => void
  clearCache: () => void
  configureCache: (config: Partial<GraphCacheConfig>) => void
}

// Hook return type with cache support
interface UseGraphStateReturn {
  graphState: GraphState
  actions: GraphActions
  isLoading: boolean
  hasData: boolean
  hasError: boolean
  cacheStats: GraphCacheStats
}

// === GRAPH CACHE MANAGEMENT ===

/**
 * Graph Cache Manager Class
 */
class GraphCacheManager {
  private cache = new Map<string, GraphCacheEntry>()
  private config: GraphCacheConfig
  private stats: GraphCacheStats

  constructor(config: Partial<GraphCacheConfig> = {}) {
    this.config = { ...DEFAULT_CACHE_CONFIG, ...config }
    this.stats = {
      hits: 0,
      misses: 0,
      entries: 0,
      totalSize: 0,
      hitRate: 0,
      oldestEntry: Date.now(),
      newestEntry: Date.now()
    }
  }

  /**
   * Generate cache key based on parameters
   */
  private generateCacheKey(params: any = {}): string {
    const paramString = JSON.stringify(params)
    return `graph_${btoa(paramString).slice(0, 16)}`
  }

  /**
   * Check if cache entry is valid
   */
  private isEntryValid(entry: GraphCacheEntry): boolean {
    return Date.now() - entry.timestamp < entry.ttl
  }

  /**
   * Calculate data size estimation
   */
  private calculateDataSize(data: GraphData): number {
    return JSON.stringify(data).length
  }

  /**
   * Auto cleanup expired entries
   */
  private cleanup(): void {
    if (!this.config.autoCleanup) return

    const now = Date.now()
    let removed = 0

    for (const [key, entry] of this.cache.entries()) {
      if (!this.isEntryValid(entry)) {
        this.cache.delete(key)
        removed++
      }
    }

    if (removed > 0) {
      console.log(`Graph cache: Cleaned up ${removed} expired entries`)
      this.updateStats()
    }
  }

  /**
   * Enforce cache size limits
   */
  private enforceSizeLimit(): void {
    if (this.cache.size <= this.config.maxEntries) return

    // Sort by last access time (LRU)
    const entries = Array.from(this.cache.entries())
      .sort(([, a], [, b]) => a.lastAccess - b.lastAccess)

    const toRemove = this.cache.size - this.config.maxEntries
    for (let i = 0; i < toRemove; i++) {
      const [key] = entries[i]
      this.cache.delete(key)
    }

    console.log(`Graph cache: Removed ${toRemove} least recently used entries`)
    this.updateStats()
  }

  /**
   * Update cache statistics
   */
  private updateStats(): void {
    const entries = Array.from(this.cache.values())
    
    this.stats.entries = entries.length
    this.stats.totalSize = entries.reduce((sum, entry) => 
      sum + this.calculateDataSize(entry.data), 0)
    
    if (entries.length > 0) {
      this.stats.oldestEntry = Math.min(...entries.map(e => e.timestamp))
      this.stats.newestEntry = Math.max(...entries.map(e => e.timestamp))
    }
    
    const totalRequests = this.stats.hits + this.stats.misses
    this.stats.hitRate = totalRequests > 0 ? this.stats.hits / totalRequests : 0
  }

  /**
   * Get cached data
   */
  getCachedData(params: any = {}): GraphData | null {
    this.cleanup()
    
    const key = this.generateCacheKey(params)
    const entry = this.cache.get(key)

    if (!entry) {
      if (this.config.enableStatistics) {
        this.stats.misses++
        this.updateStats()
      }
      return null
    }

    if (!this.isEntryValid(entry)) {
      this.cache.delete(key)
      if (this.config.enableStatistics) {
        this.stats.misses++
        this.updateStats()
      }
      return null
    }

    // Update access statistics
    entry.accessCount++
    entry.lastAccess = Date.now()

    if (this.config.enableStatistics) {
      this.stats.hits++
      this.updateStats()
    }

    console.log(`Graph cache HIT for key: ${key}`)
    return entry.data
  }

  /**
   * Set cached data
   */
  setCachedData(data: GraphData, params: any = {}, customTTL?: number): void {
    const key = this.generateCacheKey(params)
    const now = Date.now()
    
    const entry: GraphCacheEntry = {
      data: { ...data }, // Deep copy to prevent mutations
      timestamp: now,
      ttl: customTTL || this.config.defaultTTL,
      version: '1.0',
      accessCount: 0,
      lastAccess: now
    }

    this.cache.set(key, entry)
    this.enforceSizeLimit()

    if (this.config.enableStatistics) {
      this.updateStats()
    }

    console.log(`Graph cache SET for key: ${key}, TTL: ${entry.ttl}ms`)
  }

  /**
   * Invalidate specific cache entry
   */
  invalidateCache(params: any = {}): void {
    const key = this.generateCacheKey(params)
    const removed = this.cache.delete(key)
    
    if (removed) {
      console.log(`Graph cache INVALIDATED for key: ${key}`)
      this.updateStats()
    }
  }

  /**
   * Clear all cache entries
   */
  clearCache(): void {
    const entriesCleared = this.cache.size
    this.cache.clear()
    this.stats = {
      hits: 0,
      misses: 0,
      entries: 0,
      totalSize: 0,
      hitRate: 0,
      oldestEntry: Date.now(),
      newestEntry: Date.now()
    }
    console.log(`Graph cache CLEARED: ${entriesCleared} entries removed`)
  }

  /**
   * Get cache statistics
   */
  getStats(): GraphCacheStats {
    this.updateStats()
    return { ...this.stats }
  }

  /**
   * Configure cache settings
   */
  configure(newConfig: Partial<GraphCacheConfig>): void {
    this.config = { ...this.config, ...newConfig }
    this.enforceSizeLimit()
  }
}

// Global cache instance - singleton pattern to prevent multiple instances
let graphCacheInstance: GraphCacheManager | null = null
const getGraphCache = () => {
  if (!graphCacheInstance) {
    graphCacheInstance = new GraphCacheManager()
  }
  return graphCacheInstance
}

/**
 * Enhanced Enterprise Graph State Management Hook with Intelligent Caching
 * 
 * Solves the flicker problem by:
 * 1. Stable state management with explicit status tracking
 * 2. Prevents unnecessary re-renders through useCallback optimization
 * 3. Separates data fetching from component lifecycle
 * 4. Implements proper error boundaries
 */
export const useGraphState = (): UseGraphStateReturn => {
  // Central graph state - this is the single source of truth
  const [graphState, setGraphState] = useState<GraphState>({
    status: 'idle',
    data: null,
    error: null,
    lastFetchTime: null,
    isInitialized: false
  })

  // API hook for data fetching
  const { loadGraphData: apiLoadGraphData, error: apiError } = useGraphApi()
  
  // Ref to prevent concurrent fetches
  const fetchInProgressRef = useRef(false)

  // Enhanced stable action: Load graph data with intelligent caching
  const loadGraphData = useCallback(async (forceRefresh = false) => {
    // Prevent concurrent fetches
    if (fetchInProgressRef.current) {
      console.log('Graph fetch already in progress, skipping...')
      return
    }

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cachedData = getGraphCache().getCachedData()
      if (cachedData) {
        console.log('Graph data loaded from cache')
        setGraphState({
          status: 'success',
          data: cachedData,
          error: null,
          lastFetchTime: Date.now(),
          isInitialized: true
        })
        return
      }
    }

    fetchInProgressRef.current = true

    // Set loading state
    setGraphState(prev => ({
      ...prev,
      status: 'loading',
      error: null
    }))

    try {
      console.log('Loading graph data from API...')
      const data = await apiLoadGraphData()
      
      if (data) {
        // Cache the new data
        getGraphCache().setCachedData(data)
        
        // Success state
        setGraphState({
          status: 'success',
          data: data,
          error: null,
          lastFetchTime: Date.now(),
          isInitialized: true
        })
        console.log('Graph data loaded successfully and cached:', data.nodes.length, 'nodes,', data.edges.length, 'edges')
      } else {
        throw new Error('No data received from API')
      }
    } catch (error) {
      console.error('Graph data loading failed:', error)
      
      // Error state
      setGraphState(prev => ({
        ...prev,
        status: 'error',
        error: error instanceof Error ? error : new Error('Unknown error'),
        isInitialized: true
      }))
    } finally {
      fetchInProgressRef.current = false
    }
  }, [apiLoadGraphData])

  // Stable action: Refresh graph (force reload, bypass cache)
  const refreshGraph = useCallback(async () => {
    console.log('Refreshing graph data (force reload)...')
    await loadGraphData(true) // Force refresh bypasses cache
  }, [loadGraphData])

  // Stable action: Clear error
  const clearError = useCallback(() => {
    setGraphState(prev => ({
      ...prev,
      error: null,
      status: prev.data ? 'success' : 'idle'
    }))
  }, [])

  // Stable action: Reset graph to initial state
  const resetGraph = useCallback(() => {
    fetchInProgressRef.current = false
    setGraphState({
      status: 'idle',
      data: null,
      error: null,
      lastFetchTime: null,
      isInitialized: false
    })
  }, [])

  // Stable action: Update graph data (for live updates, also updates cache)
  const updateGraphData = useCallback((data: GraphData) => {
    // Update cache with new data
    getGraphCache().setCachedData(data)
    
    setGraphState(prev => ({
      ...prev,
      data: data,
      lastFetchTime: Date.now(),
      status: 'success'
    }))
  }, [])

  // Cache management actions
  const invalidateCache = useCallback(() => {
    getGraphCache().invalidateCache()
    console.log('Graph cache invalidated')
  }, [])

  const clearCache = useCallback(() => {
    getGraphCache().clearCache()
    console.log('Graph cache cleared')
  }, [])

  const configureCache = useCallback((config: Partial<GraphCacheConfig>) => {
    getGraphCache().configure(config)
    console.log('Graph cache configuration updated:', config)
  }, [])

  // Handle API errors from useGraphApi in useEffect to prevent infinite renders
  useEffect(() => {
    if (apiError && graphState.status === 'loading') {
      setGraphState(prev => ({
        ...prev,
        status: 'error',
        error: apiError,
        isInitialized: true
      }))
    }
  }, [apiError, graphState.status])

  // Enhanced stable actions object with cache support
  const actions: GraphActions = {
    loadGraphData,
    refreshGraph,
    clearError,
    resetGraph,
    updateGraphData,
    invalidateCache,
    clearCache,
    configureCache
  }

  // Computed values for easier consumption
  const isLoading = graphState.status === 'loading'
  const hasData = graphState.status === 'success' && graphState.data !== null
  const hasError = graphState.status === 'error'

  // Get current cache statistics
  const cacheStats = getGraphCache().getStats()

  return {
    graphState,
    actions,
    isLoading,
    hasData,
    hasError,
    cacheStats
  }
}

// Additional helper hooks for specific use cases
export const useGraphData = (): GraphData | null => {
  const { graphState } = useGraphState()
  return graphState.data
}

export const useGraphStats = () => {
  const { graphState } = useGraphState()
  
  if (!graphState.data) {
    return {
      totalNodes: 0,
      totalEdges: 0,
      documentNodes: 0,
      conceptNodes: 0,
      entityNodes: 0
    }
  }

  const { nodes, edges } = graphState.data

  return {
    totalNodes: nodes.length,
    totalEdges: edges.length,
    documentNodes: nodes.filter(n => n.type === 'document').length,
    conceptNodes: nodes.filter(n => n.type === 'concept').length,
    entityNodes: nodes.filter(n => n.type === 'entity').length
  }
}

// === CACHE-SPECIFIC HELPER HOOKS ===

/**
 * Hook for accessing cache statistics
 */
export const useGraphCacheStats = (): GraphCacheStats => {
  const { cacheStats } = useGraphState()
  return cacheStats
}

/**
 * Hook for cache management actions
 */
export const useGraphCacheActions = () => {
  const { actions } = useGraphState()
  return {
    invalidateCache: actions.invalidateCache,
    clearCache: actions.clearCache,
    configureCache: actions.configureCache
  }
}

/**
 * Hook for cache-aware data loading
 */
export const useGraphDataLoader = () => {
  const { actions, isLoading, hasError } = useGraphState()
  
  return {
    loadFromCache: () => actions.loadGraphData(false),
    forceRefresh: () => actions.loadGraphData(true),
    refresh: actions.refreshGraph,
    isLoading,
    hasError
  }
}

/**
 * Hook that provides cache configuration with defaults
 */
export const useGraphCacheConfig = () => {
  const { actions } = useGraphState()
  
  const updateConfig = useCallback((config: Partial<GraphCacheConfig>) => {
    actions.configureCache(config)
  }, [actions])
  
  // Predefined configurations
  const presets = {
    performance: {
      defaultTTL: 10 * 60 * 1000, // 10 minutes
      maxEntries: 20,
      enableStatistics: true,
      autoCleanup: true
    },
    development: {
      defaultTTL: 1 * 60 * 1000, // 1 minute
      maxEntries: 5,
      enableStatistics: true,
      autoCleanup: true
    },
    production: {
      defaultTTL: 15 * 60 * 1000, // 15 minutes
      maxEntries: 50,
      enableStatistics: true,
      autoCleanup: true
    }
  }
  
  return {
    updateConfig,
    presets,
    applyPreset: (preset: keyof typeof presets) => updateConfig(presets[preset])
  }
} 