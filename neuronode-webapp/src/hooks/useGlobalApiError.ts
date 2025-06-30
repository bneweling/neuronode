// K3.1.3 Global API Error Hook - Simplified re-export with convenience functions
export { useGlobalApiError, type GlobalApiError } from '@/contexts/ApiErrorContext'

import { useGlobalApiError as useGlobalApiErrorBase } from '@/contexts/ApiErrorContext'

// Convenience hook for common error scenarios
export function useApiErrorManager() {
  const globalErrorApi = useGlobalApiErrorBase()
  
  return {
    ...globalErrorApi,
    
    // Convenience methods for common error patterns
    setErrorFromResponse: (response: Record<string, unknown>, source: 'chat' | 'fileUpload' | 'graph') => {
      const error = {
        message: (response.message as string) || 'Ein unbekannter Fehler ist aufgetreten',
        error_code: response.error_code as string,
        source,
        severity: 'error' as const,
        retryable: isRetryableErrorCode(response.error_code as string),
        context: (response.context as string) || `API Response Error in ${source}`
      }
      globalErrorApi.setError(error)
    },
    
    setSimpleError: (message: string, source: 'chat' | 'fileUpload' | 'graph', retryable = false) => {
      globalErrorApi.setError({
        message,
        source,
        severity: 'error',
        retryable,
        context: `Simple error in ${source}`
      })
    },
    
    setWarning: (message: string, source: 'chat' | 'fileUpload' | 'graph') => {
      globalErrorApi.setError({
        message,
        source,
        severity: 'warning',
        retryable: false,
        context: `Warning in ${source}`
      })
    }
  }
}

// Helper function to determine if an error code is retryable
function isRetryableErrorCode(errorCode?: string): boolean {
  if (!errorCode) return false
  
  const retryableErrorCodes = [
    'LLM_2001', // API_QUOTA_EXCEEDED
    'LLM_2002', // API_RATE_LIMITED
    'LLM_2003', // API_TEMPORARILY_UNAVAILABLE
    'DB_3001',  // NEO4J_CONNECTION_FAILED
    'DB_3002',  // CHROMA_CONNECTION_FAILED
    'DB_3005',  // DATABASE_TIMEOUT
    'SYS_6001', // TEMPORARY_SYSTEM_ERROR
    'SYS_6002', // SERVICE_TEMPORARILY_UNAVAILABLE
    'PROC_4005' // PROCESSING_TIMEOUT
  ]
  
  return retryableErrorCodes.includes(errorCode)
} 