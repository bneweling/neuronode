// K3.1.3 Document API Hook - Global Error Context Integration
import { useCallback, useState } from 'react'

import { useGlobalApiError } from '@/contexts/ApiErrorContext'

interface DocumentApiOptions {
  onError?: (error: unknown) => void
  onRetry?: (retryCount: number) => void
  onSuccess?: () => void
}

export interface DocumentApiReturn {
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
 * K3.1.3 Document API Hook with Global Error Context
 * Specialized hook for document operations that integrates with the global error management system
 */
export function useDocumentApi(options: DocumentApiOptions = {}): DocumentApiReturn {
  const { onError, onSuccess } = options
  const { setError, clearError: clearGlobalError } = useGlobalApiError()
  const [isLoading, setIsLoading] = useState(false)

  /**
   * Determine if an error is retryable based on K2 backend error codes for documents
   */
  const isRetryableError = useCallback((errorCode?: string): boolean => {
    if (!errorCode) return false

    const retryableErrors = [
      'DOC_1005', // DOCUMENT_PROCESSING_TIMEOUT - Can retry
      'LLM_2001', // LLM_API_QUOTA_EXCEEDED - Auto-retry
      'LLM_2002', // LLM_API_RATE_LIMITED - Auto-retry
      'DB_3001',  // NEO4J_CONNECTION_FAILED - Retry database
      'DB_3005',  // DATABASE_TIMEOUT - Retry timeout
      'PROC_4005', // PROCESSING_TIMEOUT - Can retry processing
      'SYS_6001'  // TEMPORARY_SYSTEM_ERROR - System retry
    ]

    return retryableErrors.includes(errorCode)
  }, [])

  /**
   * Parse API error response into global error format for documents
   */
  const parseApiError = useCallback((error: unknown) => {
    let errorCode = 'UNKNOWN_ERROR'
    let message = 'Unbekannter Fehler beim Dokument-Upload.'
    let retryable = false

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const errorObj = error as Record<string, any>

    // Parse different error formats
    if (errorObj?.response?.data) {
      const data = errorObj.response.data
      errorCode = data.error_code || data.error || 'DOCUMENT_ERROR'
      
      // Enhanced messages for document-specific errors
      switch (errorCode) {
        case 'DOC_1001':
          message = 'Dateiformat nicht unterstützt. Bitte wählen Sie eine PDF, DOCX, TXT oder andere unterstützte Datei.'
          break
        case 'DOC_1002':
          message = 'Datei ist zu groß. Maximale Dateigröße ist 50MB.'
          break
        case 'DOC_1003':
          message = 'Datei konnte nicht gelesen werden. Überprüfen Sie, ob die Datei beschädigt ist.'
          break
        case 'DOC_1004':
          message = 'Dateiinhalt ist ungültig oder leer.'
          break
        case 'DOC_1005':
          message = 'Dokument-Verarbeitung dauert länger als erwartet. Bitte versuchen Sie es erneut.'
          break
        case 'PROC_4001':
          message = 'Textextraktion fehlgeschlagen. Die Datei könnte beschädigt oder verschlüsselt sein.'
          break
        case 'PROC_4002':
          message = 'Dokumentenklassifikation fehlgeschlagen. Versuchen Sie es mit einer anderen Datei.'
          break
        case 'PROC_4003':
          message = 'Entitätserkennung fehlgeschlagen. Das Dokument enthält möglicherweise unverständlichen Text.'
          break
        default:
          message = data.detail || data.message || 'Fehler beim Dokument-Upload.'
      }
      
      retryable = isRetryableError(errorCode)
    } else if (errorObj?.code === 'NETWORK_ERROR' || errorObj?.message?.includes('Network Error')) {
      errorCode = 'NETWORK_ERROR'
      message = 'Netzwerkfehler beim Upload. Bitte überprüfen Sie Ihre Internetverbindung.'
      retryable = true
    } else if (errorObj?.message?.includes('File too large')) {
      errorCode = 'DOC_1002'
      message = 'Datei ist zu groß für den Upload.'
      retryable = false
    } else if (errorObj?.message) {
      message = errorObj.message
      retryable = false
    }

    return {
      message,
      error_code: errorCode,
      source: 'fileUpload' as const,
      severity: retryable ? 'warning' as const : 'error' as const,
      retryable,
      context: `Document Upload Error: ${errorCode}`
    }
  }, [isRetryableError])

  /**
   * Execute API call with intelligent error handling for documents
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

    // Clear any existing file upload errors
    clearGlobalError('fileUpload')

    try {
      const result = await apiCall()
      setIsLoading(false)

      if (onSuccess) {
        onSuccess()
      }

      return result
    } catch (error) {
      setIsLoading(false)
      
      const globalError = parseApiError(error)
      
      // Enhanced logging for document errors
      console.error('Document API Error:', {
        error_code: globalError.error_code,
        message: globalError.message,
        retryable: globalError.retryable,
        context: context || globalError.context,
        file_related: true
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
    }
  }, [setError, clearGlobalError, parseApiError, onError, onSuccess])

  /**
   * Clear document-specific errors
   */
  const clearError = useCallback((): void => {
    clearGlobalError('fileUpload')
  }, [clearGlobalError])

  return {
    isLoading,
    executeWithErrorHandling,
    clearError
  }
}

/**
 * Legacy compatibility - exports useDocumentApiError for existing code
 */
export const useDocumentApiError = useDocumentApi 