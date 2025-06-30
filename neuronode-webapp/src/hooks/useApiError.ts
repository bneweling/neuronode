import { useState, useCallback } from 'react';

import { BackendError } from '@/components/error/ErrorBoundary';

// K2 Error Code definitions based on backend research
export enum K2ErrorCode {
  // Document Processing Errors
  DOCUMENT_TYPE_UNSUPPORTED = 'DOCUMENT_TYPE_UNSUPPORTED',
  DOCUMENT_SIZE_EXCEEDED = 'DOCUMENT_SIZE_EXCEEDED',
  DOCUMENT_PARSING_FAILED = 'DOCUMENT_PARSING_FAILED',
  DOCUMENT_CONTENT_INVALID = 'DOCUMENT_CONTENT_INVALID',
  DOCUMENT_NOT_FOUND = 'DOCUMENT_NOT_FOUND',
  DOCUMENT_PERMISSION_DENIED = 'DOCUMENT_PERMISSION_DENIED',

  // LLM Service Errors
  LLM_API_QUOTA_EXCEEDED = 'LLM_API_QUOTA_EXCEEDED',
  LLM_API_TIMEOUT = 'LLM_API_TIMEOUT',
  LLM_SERVICE_UNAVAILABLE = 'LLM_SERVICE_UNAVAILABLE',
  LLM_INVALID_RESPONSE = 'LLM_INVALID_RESPONSE',
  LLM_RATE_LIMIT_EXCEEDED = 'LLM_RATE_LIMIT_EXCEEDED',
  LLM_AUTHENTICATION_FAILED = 'LLM_AUTHENTICATION_FAILED',

  // Database Errors
  NEO4J_CONNECTION_FAILED = 'NEO4J_CONNECTION_FAILED',
  NEO4J_QUERY_FAILED = 'NEO4J_QUERY_FAILED',
  NEO4J_CONSTRAINT_VIOLATION = 'NEO4J_CONSTRAINT_VIOLATION',
  CHROMA_CONNECTION_FAILED = 'CHROMA_CONNECTION_FAILED',
  DATABASE_TIMEOUT = 'DATABASE_TIMEOUT',

  // Processing Pipeline Errors
  EXTRACTION_FAILED = 'EXTRACTION_FAILED',
  CLASSIFICATION_FAILED = 'CLASSIFICATION_FAILED',
  RELATIONSHIP_DISCOVERY_FAILED = 'RELATIONSHIP_DISCOVERY_FAILED',
  PIPELINE_INTERRUPTED = 'PIPELINE_INTERRUPTED',
  PROCESSING_TIMEOUT = 'PROCESSING_TIMEOUT',

  // Query Processing Errors
  QUERY_PARSING_FAILED = 'QUERY_PARSING_FAILED',
  QUERY_EXPANSION_FAILED = 'QUERY_EXPANSION_FAILED',
  RESPONSE_SYNTHESIS_FAILED = 'RESPONSE_SYNTHESIS_FAILED',
  SEARCH_FAILED = 'SEARCH_FAILED',

  // System Errors
  SYSTEM_OVERLOAD = 'SYSTEM_OVERLOAD',
  CONFIGURATION_ERROR = 'CONFIGURATION_ERROR',
  DEPENDENCY_UNAVAILABLE = 'DEPENDENCY_UNAVAILABLE',
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR'
}

interface ApiErrorState {
  error: BackendError | null;
  isLoading: boolean;
  retryCount: number;
  canRetry: boolean;
}

interface UseApiErrorOptions {
  maxRetries?: number;
  retryDelay?: number;
  onError?: (error: BackendError) => void;
  onRetry?: (retryCount: number) => void;
  onSuccess?: () => void;
}

interface UseApiErrorReturn extends ApiErrorState {
  executeWithErrorHandling: <T>(
    apiCall: () => Promise<T>,
    options?: {
      retryable?: boolean;
      context?: string;
    }
  ) => Promise<T | null>;
  retry: () => Promise<void>;
  clearError: () => void;
  isRetryableError: (error: BackendError) => boolean;
}

/**
 * K3.1 API Error Hook - Intelligent error handling with K2 backend integration
 * Provides automatic retry logic, error classification, and Material-UI integration
 */
export const useApiError = (options: UseApiErrorOptions = {}): UseApiErrorReturn => {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    onError,
    onRetry,
    onSuccess
  } = options;

  const [errorState, setErrorState] = useState<ApiErrorState>({
    error: null,
    isLoading: false,
    retryCount: 0,
    canRetry: false
  });

  const [lastApiCall, setLastApiCall] = useState<{
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fn: () => Promise<any>;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    options?: any;
  } | null>(null);

  /**
   * Determine if an error is retryable based on K2 error classification
   */
  const isRetryableError = useCallback((error: BackendError): boolean => {
    // Network/connection errors are always retryable
    if (error.status_code >= 500 && error.status_code < 600) {
      return true;
    }

    // Check specific K2 error codes
    const retryableErrors: K2ErrorCode[] = [
      K2ErrorCode.LLM_API_QUOTA_EXCEEDED,
      K2ErrorCode.LLM_API_TIMEOUT,
      K2ErrorCode.LLM_SERVICE_UNAVAILABLE,
      K2ErrorCode.LLM_RATE_LIMIT_EXCEEDED,
      K2ErrorCode.NEO4J_CONNECTION_FAILED,
      K2ErrorCode.CHROMA_CONNECTION_FAILED,
      K2ErrorCode.DATABASE_TIMEOUT,
      K2ErrorCode.SYSTEM_OVERLOAD,
      K2ErrorCode.DEPENDENCY_UNAVAILABLE,
      K2ErrorCode.PROCESSING_TIMEOUT
    ];

    return retryableErrors.includes(error.error_code as K2ErrorCode);
  }, []);

  /**
   * Parse API error response into BackendError format
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const parseApiError = useCallback((error: any): BackendError => {
    // If it's already a BackendError, return as is
    if (error && typeof error === 'object' && 'error_code' in error) {
      return error as BackendError;
    }

    // Handle fetch/axios errors
    if (error?.response) {
      const response = error.response;
      return {
        error_code: response.data?.error_code || response.data?.error || 'API_ERROR',
        message: response.data?.detail || response.data?.message || response.statusText,
        details: response.data?.details,
        status_code: response.status,
        retryable: isRetryableError({
          error_code: response.data?.error_code || 'API_ERROR',
          message: '',
          status_code: response.status
        } as BackendError)
      };
    }

    // Handle network errors
    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
      return {
        error_code: 'NETWORK_ERROR',
        message: 'Netzwerkfehler - Bitte überprüfen Sie Ihre Internetverbindung.',
        status_code: 0,
        retryable: true
      };
    }

    // Generic error fallback
    return {
      error_code: 'UNKNOWN_ERROR',
      message: error?.message || 'Ein unbekannter Fehler ist aufgetreten.',
      status_code: 500,
      retryable: false
    };
  }, [isRetryableError]);

  /**
   * Execute API call with intelligent error handling and retry logic
   */
  const executeWithErrorHandling = useCallback(async <T>(
    apiCall: () => Promise<T>,
    callOptions: {
      retryable?: boolean;
      context?: string;
    } = {}
  ): Promise<T | null> => {
    const { retryable, context } = callOptions;

    setErrorState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    // Store the API call for potential retry
    setLastApiCall({ fn: apiCall, options: callOptions });

    try {
      const result = await apiCall();
      
      // Success - reset error state
      setErrorState({
        error: null,
        isLoading: false,
        retryCount: 0,
        canRetry: false
      });

      if (onSuccess) {
        onSuccess();
      }

      return result;
    } catch (error) {
      const backendError = parseApiError(error);
      const canRetryThis = retryable !== false && isRetryableError(backendError);
      
      console.error(`API Error${context ? ` in ${context}` : ''}:`, {
        error_code: backendError.error_code,
        message: backendError.message,
        status_code: backendError.status_code,
        retryable: canRetryThis,
        retryCount: errorState.retryCount
      });

      setErrorState(prev => ({
        error: backendError,
        isLoading: false,
        retryCount: prev.retryCount,
        canRetry: canRetryThis && prev.retryCount < maxRetries
      }));

      if (onError) {
        onError(backendError);
      }

      // Auto-retry for specific errors (like rate limits)
      if (canRetryThis && 
          errorState.retryCount < maxRetries && 
          [K2ErrorCode.LLM_API_QUOTA_EXCEEDED, K2ErrorCode.LLM_RATE_LIMIT_EXCEEDED].includes(backendError.error_code as K2ErrorCode)) {
        
        console.log(`Auto-retrying after ${retryDelay}ms for error: ${backendError.error_code}`);
        
        setTimeout(() => {
          retry();
        }, retryDelay * Math.pow(2, errorState.retryCount)); // Exponential backoff
      }

      return null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [errorState.retryCount, maxRetries, retryDelay, parseApiError, isRetryableError, onError, onSuccess]);

  /**
   * Manual retry function
   */
  const retry = useCallback(async (): Promise<void> => {
    if (!lastApiCall || !errorState.canRetry) {
      return;
    }

    setErrorState(prev => ({
      ...prev,
      retryCount: prev.retryCount + 1,
      isLoading: true
    }));

    if (onRetry) {
      onRetry(errorState.retryCount + 1);
    }

    // Re-execute the last API call
    await executeWithErrorHandling(lastApiCall.fn, lastApiCall.options);
  }, [lastApiCall, errorState.canRetry, errorState.retryCount, executeWithErrorHandling, onRetry]);

  /**
   * Clear error state
   */
  const clearError = useCallback((): void => {
    setErrorState({
      error: null,
      isLoading: false,
      retryCount: 0,
      canRetry: false
    });
    setLastApiCall(null);
  }, []);

  return {
    ...errorState,
    executeWithErrorHandling,
    retry,
    clearError,
    isRetryableError
  };
};

/**
 * Convenience hook for chat API calls with specific error handling
 */
export const useChatApiError = (options?: UseApiErrorOptions) => {
  return useApiError({
    maxRetries: 5, // Chat is more tolerant of retries
    retryDelay: 2000, // Longer delay for LLM services
    ...options
  });
};

/**
 * Convenience hook for document upload with specific error handling
 */
export const useDocumentApiError = (options?: UseApiErrorOptions) => {
  return useApiError({
    maxRetries: 2, // Document processing is less retryable
    retryDelay: 1000,
    ...options
  });
};

/**
 * Convenience hook for graph queries with specific error handling
 */
export const useGraphApiError = (options?: UseApiErrorOptions) => {
  return useApiError({
    maxRetries: 3,
    retryDelay: 1500,
    ...options
  });
}; 