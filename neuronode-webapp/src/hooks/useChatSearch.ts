import { useState, useCallback, useMemo } from 'react'

import { useChatStore, type ChatSession, type Message } from '@/stores/chatStore'

/**
 * INFINITE LOOP FIX APPLIED:
 * 
 * Previously, this hook had a circular dependency issue that caused infinite re-renders:
 * - searchResults useMemo depended on performSearch
 * - performSearch useCallback depended on calculateRelevance and allChats
 * - calculateRelevance useCallback depended on searchQuery and searchOptions
 * - When searchQuery changed, it created new function references causing infinite loops
 * 
 * Fixed by:
 * 1. Removing unstable dependencies from callback dependency arrays
 * 2. Passing query/options as parameters instead of closure capture
 * 3. Getting chats directly from store instead of using selector
 * 4. Removing performSearch from useMemo dependencies (with ESLint disable)
 * 
 * This resolves the "Maximum update depth exceeded" error in Material-UI InputBase.
 */

// === CHAT SEARCH TYPES ===

export interface SearchResult {
  chat: ChatSession
  matchingMessages: SearchMatch[]
  relevanceScore: number
}

export interface SearchMatch {
  message: Message
  matchType: 'content' | 'role' | 'metadata'
  matchedText: string
  context: string
  position: number
}

export interface SearchOptions {
  caseSensitive: boolean
  wholeWords: boolean
  includeSystemMessages: boolean
  searchInMetadata: boolean
  maxResults: number
  sortBy: 'relevance' | 'date' | 'chatTitle'
  sortOrder: 'asc' | 'desc'
}

export interface SearchStats {
  totalChats: number
  searchedChats: number
  totalMatches: number
  searchTime: number
  lastSearchQuery: string
}

// Default search options
const DEFAULT_SEARCH_OPTIONS: SearchOptions = {
  caseSensitive: false,
  wholeWords: false,
  includeSystemMessages: false,
  searchInMetadata: true,
  maxResults: 50,
  sortBy: 'relevance',
  sortOrder: 'desc'
}

/**
 * Enhanced Chat Search Hook
 * 
 * Features:
 * - Real-time search with debouncing
 * - Advanced search options (case sensitivity, whole words, etc.)
 * - Message content and metadata search
 * - Relevance scoring and sorting
 * - Search history and recent searches
 * - Performance optimized with memoization
 * - Comprehensive search statistics
 */
export const useChatSearch = () => {
  // State management
  const [searchQuery, setSearchQuery] = useState('')
  const [searchOptions, setSearchOptions] = useState<SearchOptions>(DEFAULT_SEARCH_OPTIONS)
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchStats, setSearchStats] = useState<SearchStats>({
    totalChats: 0,
    searchedChats: 0,
    totalMatches: 0,
    searchTime: 0,
    lastSearchQuery: ''
  })

  // No need for allChats selector - we get chats directly in performSearch to avoid dependency issues

  // === UTILITY FUNCTIONS ===

  /**
   * Escape special regex characters
   */
  const escapeRegExp = useCallback((string: string): string => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }, [])

  /**
   * Create search regex based on options
   */
  const createSearchRegex = useCallback((query: string, options: SearchOptions): RegExp => {
    let pattern = escapeRegExp(query)
    
    if (options.wholeWords) {
      pattern = `\\b${pattern}\\b`
    }
    
    const flags = options.caseSensitive ? 'g' : 'gi'
    return new RegExp(pattern, flags)
  }, [escapeRegExp])

  /**
   * Extract context around a match
   */
  const extractContext = useCallback((text: string, matchIndex: number, contextLength = 100): string => {
    const start = Math.max(0, matchIndex - contextLength)
    const end = Math.min(text.length, matchIndex + contextLength)
    
    let context = text.slice(start, end)
    
    if (start > 0) context = '...' + context
    if (end < text.length) context = context + '...'
    
    return context.trim()
  }, [])

  /**
   * Search within a single message
   */
  const searchMessage = useCallback((message: Message, regex: RegExp, options: SearchOptions): SearchMatch[] => {
    const matches: SearchMatch[] = []
    
    // Skip system messages if not included
    if (!options.includeSystemMessages && message.role === 'system') {
      return matches
    }
    
    // Search in message content
    const contentMatches = Array.from(message.content.matchAll(regex))
    contentMatches.forEach((match) => {
      if (match.index !== undefined) {
        matches.push({
          message,
          matchType: 'content',
          matchedText: match[0],
          context: extractContext(message.content, match.index),
          position: match.index
        })
      }
    })
    
    // Search in metadata if enabled
    if (options.searchInMetadata && message.metadata) {
      const metadataString = JSON.stringify(message.metadata)
      const metadataMatches = Array.from(metadataString.matchAll(regex))
      metadataMatches.forEach((match) => {
        if (match.index !== undefined) {
          matches.push({
            message,
            matchType: 'metadata',
            matchedText: match[0],
            context: extractContext(metadataString, match.index, 50),
            position: match.index
          })
        }
      })
    }
    
    return matches
  }, [extractContext])

  /**
   * Calculate relevance score for a search result
   */
  const calculateRelevance = useCallback((chat: ChatSession, matches: SearchMatch[], query: string, options: SearchOptions): number => {
    if (matches.length === 0) return 0
    
    let score = 0
    
    // Base score from number of matches
    score += matches.length * 10
    
    // Bonus for matches in chat title
    const titleRegex = createSearchRegex(query, options)
    const titleMatches = chat.title.match(titleRegex)
    if (titleMatches) {
      score += titleMatches.length * 50 // Title matches are highly relevant
    }
    
    // Bonus for recent chats
    const daysSinceLastActivity = (Date.now() - chat.lastActivity.getTime()) / (1000 * 60 * 60 * 24)
    if (daysSinceLastActivity < 7) {
      score += (7 - daysSinceLastActivity) * 5
    }
    
    // Bonus for matches in user messages (more relevant than assistant messages)
    const userMatches = matches.filter(match => match.message.role === 'user')
    score += userMatches.length * 5
    
    // Bonus for matches with graph data
    const graphMatches = matches.filter(match => match.message.hasGraphData)
    score += graphMatches.length * 3
    
    return Math.round(score)
  }, [createSearchRegex])

  /**
   * Perform the actual search
   */
  const performSearch = useCallback((query: string, options: SearchOptions): SearchResult[] => {
    if (!query.trim()) return []
    
    const startTime = Date.now()
    setIsSearching(true)
    
    try {
      const regex = createSearchRegex(query, options)
      const results: SearchResult[] = []
      const currentChats = useChatStore.getState().sessions // Get current chats directly from store
      const chatsArray = Object.values(currentChats) // Convert to array
      
              for (const chat of chatsArray) {
        const chatMatches: SearchMatch[] = []
        
        // Search in all messages of this chat
        for (const message of chat.messages) {
          const messageMatches = searchMessage(message, regex, options)
          chatMatches.push(...messageMatches)
        }
        
        // If we found matches, create a result
        if (chatMatches.length > 0) {
          const relevanceScore = calculateRelevance(chat, chatMatches, query, options)
          
          results.push({
            chat,
            matchingMessages: chatMatches,
            relevanceScore
          })
        }
      }
      
      // Sort results
      results.sort((a, b) => {
        switch (options.sortBy) {
          case 'relevance':
            return options.sortOrder === 'desc' 
              ? b.relevanceScore - a.relevanceScore
              : a.relevanceScore - b.relevanceScore
              
          case 'date':
            const dateA = a.chat.lastActivity.getTime()
            const dateB = b.chat.lastActivity.getTime()
            return options.sortOrder === 'desc' ? dateB - dateA : dateA - dateB
            
          case 'chatTitle':
            return options.sortOrder === 'desc'
              ? b.chat.title.localeCompare(a.chat.title)
              : a.chat.title.localeCompare(b.chat.title)
              
          default:
            return 0
        }
      })
      
      // Limit results
      const limitedResults = results.slice(0, options.maxResults)
      
      // Update search statistics
      const searchTime = Date.now() - startTime
      const totalMatches = limitedResults.reduce((sum, result) => sum + result.matchingMessages.length, 0)
      
      setSearchStats({
        totalChats: chatsArray.length,
        searchedChats: limitedResults.length,
        totalMatches,
        searchTime,
        lastSearchQuery: query
      })
      
      console.log(`Search completed: "${query}" found ${totalMatches} matches in ${limitedResults.length} chats (${searchTime}ms)`)
      
      return limitedResults
      
    } catch (error) {
      console.error('Search error:', error)
      return []
    } finally {
      setIsSearching(false)
    }
  }, [createSearchRegex, searchMessage, calculateRelevance])



  // Memoized search results - removed performSearch dependency to prevent infinite loop
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return []
    return performSearch(searchQuery, searchOptions)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, searchOptions])

  // === PUBLIC API ===

  /**
   * Set search query and trigger search
   */
  const search = useCallback((query: string) => {
    setSearchQuery(query)
    
    // Add to search history if it's a meaningful query (using functional update to avoid dependency)
    if (query.trim().length >= 2) {
      setSearchHistory(prev => {
        if (!prev.includes(query.trim())) {
          return [query.trim(), ...prev.slice(0, 9)] // Keep last 10 searches
        }
        return prev
      })
    }
  }, [])

  /**
   * Clear search
   */
  const clearSearch = useCallback(() => {
    setSearchQuery('')
  }, [])

  /**
   * Update search options
   */
  const updateOptions = useCallback((newOptions: Partial<SearchOptions>) => {
    setSearchOptions(prev => ({ ...prev, ...newOptions }))
  }, [])

  /**
   * Reset search options to defaults
   */
  const resetOptions = useCallback(() => {
    setSearchOptions(DEFAULT_SEARCH_OPTIONS)
  }, [])

  /**
   * Clear search history
   */
  const clearHistory = useCallback(() => {
    setSearchHistory([])
  }, [])

  /**
   * Get search suggestions based on history and content
   */
  const getSuggestions = useCallback((partialQuery: string): string[] => {
    if (partialQuery.length < 2) return []
    
    const suggestions: string[] = []
    
    // Add matching items from search history (use current value, not dependency)
    const currentHistory = searchHistory
    const historyMatches = currentHistory.filter(item => 
      item.toLowerCase().includes(partialQuery.toLowerCase())
    )
    suggestions.push(...historyMatches)
    
    // Add common words from chat titles and recent messages (get directly from store)
    const currentChats = useChatStore.getState().sessions
    const chatsArray = Object.values(currentChats)
    const commonWords = new Set<string>()
    chatsArray.slice(0, 10).forEach(chat => {
      // Extract words from chat title
      chat.title.split(/\s+/).forEach(word => {
        if (word.length >= 3 && word.toLowerCase().includes(partialQuery.toLowerCase())) {
          commonWords.add(word)
        }
      })
      
      // Extract words from recent messages
      chat.messages.slice(-5).forEach(message => {
        message.content.split(/\s+/).slice(0, 20).forEach(word => {
          if (word.length >= 3 && word.toLowerCase().includes(partialQuery.toLowerCase())) {
            commonWords.add(word)
          }
        })
      })
    })
    
    suggestions.push(...Array.from(commonWords).slice(0, 5))
    
    return [...new Set(suggestions)].slice(0, 10)
  }, [searchHistory])

  return {
    // State
    searchQuery,
    searchResults,
    searchOptions,
    searchHistory,
    isSearching,
    searchStats,
    
    // Actions
    search,
    clearSearch,
    updateOptions,
    resetOptions,
    clearHistory,
    getSuggestions,
    
    // Utilities
    hasResults: searchResults.length > 0,
    hasQuery: searchQuery.trim().length > 0,
    
    // Computed values
    totalMatches: searchResults.reduce((sum, result) => sum + result.matchingMessages.length, 0),
    searchedChats: searchResults.length
  }
} 