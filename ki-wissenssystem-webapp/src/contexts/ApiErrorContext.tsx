'use client'

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'

// K3.1.3 Global Error Types - Aligned with K2 Backend Exception System
export interface GlobalApiError {
  id: string
  message: string
  error_code?: string
  source: 'chat' | 'fileUpload' | 'graph' | 'global' | 'system'
  severity: 'error' | 'warning' | 'info'
  retryable: boolean
  timestamp: number
  context?: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details?: Record<string, any>
}

interface ApiErrorContextType {
  // Current errors by source
  errors: Record<string, GlobalApiError | null>
  
  // Error management functions
  setError: (error: Omit<GlobalApiError, 'id' | 'timestamp'>) => void
  clearError: (source: string) => void
  clearAllErrors: () => void
  
  // Error retrieval functions
  getError: (source: string) => GlobalApiError | null
  hasError: (source?: string) => boolean
  hasRetryableError: (source: string) => boolean
}

const ApiErrorContext = createContext<ApiErrorContextType | undefined>(undefined)

// K3.1.3 Global Error Context Provider
export function ApiErrorContextProvider({ children }: { children: ReactNode }) {
  const [errors, setErrors] = useState<Record<string, GlobalApiError | null>>({})

  const setError = useCallback((errorData: Omit<GlobalApiError, 'id' | 'timestamp'>) => {
    const error: GlobalApiError = {
      ...errorData,
      id: `${errorData.source}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now()
    }

    setErrors(prev => ({
      ...prev,
      [errorData.source]: error
    }))

    // Log structured error for debugging
    console.error('Global API Error:', {
      source: error.source,
      error_code: error.error_code,
      message: error.message,
      severity: error.severity,
      retryable: error.retryable,
      context: error.context
    })
  }, [])

  const clearError = useCallback((source: string) => {
    setErrors(prev => ({
      ...prev,
      [source]: null
    }))
  }, [])

  const clearAllErrors = useCallback(() => {
    setErrors({})
  }, [])

  const getError = useCallback((source: string): GlobalApiError | null => {
    return errors[source] || null
  }, [errors])

  const hasError = useCallback((source?: string): boolean => {
    if (source) {
      return errors[source] !== null && errors[source] !== undefined
    }
    return Object.values(errors).some(error => error !== null && error !== undefined)
  }, [errors])

  const hasRetryableError = useCallback((source: string): boolean => {
    const error = errors[source]
    return error ? error.retryable : false
  }, [errors])

  const contextValue: ApiErrorContextType = {
    errors,
    setError,
    clearError,
    clearAllErrors,
    getError,
    hasError,
    hasRetryableError
  }

  return (
    <ApiErrorContext.Provider value={contextValue}>
      {children}
    </ApiErrorContext.Provider>
  )
}

// K3.1.3 Global Error Context Hook
export function useGlobalApiError() {
  const context = useContext(ApiErrorContext)
  if (context === undefined) {
    throw new Error('useGlobalApiError must be used within an ApiErrorContextProvider')
  }
  return context
}

export default ApiErrorContext 