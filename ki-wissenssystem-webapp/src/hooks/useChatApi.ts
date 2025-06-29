// K3.1.3 Chat API Hook - Global Error Context Integration
import { useCallback, useState } from 'react'

import { useGlobalApiError } from '@/contexts/ApiErrorContext'

interface ChatApiOptions {
  onError?: (error: unknown) => void
  onRetry?: (retryCount: number) => void
  onSuccess?: () => void
}

export interface ChatApiReturn {
  isLoading: boolean
  executeWithErrorHandling: <T>(
    apiCall: () => Promise<T>,
    options?: {
      retryable?: boolean
      context?: string
    }
  ) => Promise<T | null>
  clearError: () => void
}

/**
 * K3.1.3 Chat API Hook with Global Error Context
 * Specialized hook for chat operations that integrates with the global error management system
 */
export function useChatApi(options: ChatApiOptions = {}): ChatApiReturn {
  const { onError, onSuccess } = options
  const { setError, clearError: clearGlobalError } = useGlobalApiError()
  const [isLoading, setIsLoading] = useState(false)

  /**
   * Determine if an error is retryable based on K2 backend error codes
   */
  const isRetryableError = useCallback((errorCode?: string): boolean => {
    if (!errorCode) return false

    const retryableErrors = [
      'LLM_2001', // LLM_API_QUOTA_EXCEEDED
      'LLM_2002', // LLM_API_RATE_LIMITED
      'LLM_2003', // LLM_API_TEMPORARILY_UNAVAILABLE
      'DB_3001',  // NEO4J_CONNECTION_FAILED
      'DB_3005',  // DATABASE_TIMEOUT
      'SYS_6001', // TEMPORARY_SYSTEM_ERROR
      'SYS_6002'  // SERVICE_TEMPORARILY_UNAVAILABLE
    ]

    return retryableErrors.includes(errorCode)
  }, [])

  /**
   * Parse API error response into global error format
   */
  const parseApiError = useCallback((error: unknown) => {
    let errorCode = 'UNKNOWN_ERROR'
    let message = 'Ein unbekannter Fehler ist aufgetreten.'
    let retryable = false

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const errorObj = error as Record<string, any>

    // Parse different error formats
    if (errorObj?.response?.data) {
      const data = errorObj.response.data
      errorCode = data.error_code || data.error || 'API_ERROR'
      message = data.detail || data.message || 'API-Fehler aufgetreten.'
      retryable = isRetryableError(errorCode)
    } else if (errorObj?.code === 'NETWORK_ERROR' || errorObj?.message?.includes('Network Error')) {
      errorCode = 'NETWORK_ERROR'
      message = 'Netzwerkfehler - Bitte überprüfen Sie Ihre Internetverbindung.'
      retryable = true
    } else if (errorObj?.message) {
      message = errorObj.message
      retryable = false
    }

    return {
      message,
      error_code: errorCode,
      source: 'chat' as const,
      severity: retryable ? 'warning' as const : 'error' as const,
      retryable,
      context: `Chat API Error: ${errorCode}`
    }
  }, [isRetryableError])

  /**
   * Execute API call with intelligent error handling
   * P2_PERFORMANCE_POLISH: Enhanced state management to prevent button disabled state issues
   */
  const executeWithErrorHandling = useCallback(async <T>(
    apiCall: () => Promise<T>,
    callOptions: {
      retryable?: boolean
      context?: string
    } = {}
  ): Promise<T | null> => {
    const { context } = callOptions

    setIsLoading(true)

    // Clear any existing chat errors
    clearGlobalError('chat')

    try {
      const result = await apiCall()
      
      if (onSuccess) {
        onSuccess()
      }

      return result
    } catch (error) {
      const globalError = parseApiError(error)
      
      // Log for debugging
      console.error('Chat API Error:', {
        error_code: globalError.error_code,
        message: globalError.message,
        retryable: globalError.retryable,
        context: context || globalError.context
      })

      // Set global error with enhanced context
      setError({
        ...globalError,
        context: context || globalError.context
      })

      if (onError) {
        onError(error)
      }

      return null
    } finally {
      // P2_PERFORMANCE_POLISH: Always reset loading state in finally block
      // This ensures the chat-send button becomes enabled again even if errors occur
      setIsLoading(false)
    }
  }, [setError, clearGlobalError, parseApiError, onError, onSuccess])

  /**
   * Clear chat-specific errors
   */
  const clearError = useCallback((): void => {
    clearGlobalError('chat')
  }, [clearGlobalError])

  return {
    isLoading,
    executeWithErrorHandling,
    clearError
  }
}

/**
 * Legacy compatibility - exports useChatApiError for existing code
 */
export const useChatApiError = useChatApi 