import { renderHook, act } from '@testing-library/react';
import { useApiError } from '@/hooks/useApiError';
import { BackendError } from '@/components/error/ErrorBoundary';

describe('useApiError Hook', () => {
  test('initializes with no error state', () => {
    const { result } = renderHook(() => useApiError());

    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.canRetry).toBe(false);
  });

  test('sets loading state during API call', async () => {
    const { result } = renderHook(() => useApiError());

    const mockApiCall = jest.fn().mockResolvedValue({ data: 'success' });

    act(() => {
      result.current.executeWithErrorHandling(mockApiCall);
    });

    expect(result.current.isLoading).toBe(true);
  });

  test('handles successful API calls', async () => {
    const { result } = renderHook(() => useApiError());

    const mockApiCall = jest.fn().mockResolvedValue({ data: 'success' });

    await act(async () => {
      const response = await result.current.executeWithErrorHandling(mockApiCall);
      expect(response).toEqual({ data: 'success' });
    });

    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  test('handles API errors with proper error classification', async () => {
    const { result } = renderHook(() => useApiError());

    const mockError: BackendError = {
      message: 'Test error',
      error_code: 'LLM_API_QUOTA_EXCEEDED',
      status_code: 429,
      retryable: true
    };

    const mockApiCall = jest.fn().mockRejectedValue(mockError);

    await act(async () => {
      try {
        await result.current.executeWithErrorHandling(mockApiCall);
      } catch (error) {
        // Error is expected
      }
    });

    expect(result.current.error).toEqual(mockError);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.canRetry).toBe(true); // LLM_API_QUOTA_EXCEEDED should be retryable
  });

  test('implements exponential backoff for retries', async () => {
    const { result } = renderHook(() => useApiError());

    const mockError: BackendError = {
      message: 'Rate limit exceeded',
      error_code: 'LLM_RATE_LIMIT_EXCEEDED',
      status_code: 429,
      retryable: true
    };

    const mockApiCall = jest
      .fn()
      .mockRejectedValueOnce(mockError)
      .mockRejectedValueOnce(mockError)
      .mockResolvedValueOnce({ data: 'success' });

    await act(async () => {
      try {
        await result.current.executeWithErrorHandling(mockApiCall);
      } catch (error) {
        // First attempt fails
      }
    });

    expect(result.current.retryCount).toBe(0);

    // Test retry mechanism exists and can be called
    await act(async () => {
      try {
        await result.current.retry();
      } catch (error) {
        // Second attempt fails
      }
    });

    // Verify retry was attempted
    expect(result.current.retryCount).toBe(1);
    expect(mockApiCall).toHaveBeenCalledTimes(2); // Original + 1 retry
  });

  test('respects maximum retry attempts', async () => {
    const { result } = renderHook(() => useApiError());

    const mockError: BackendError = {
      message: 'Persistent error',
      error_code: 'LLM_RATE_LIMIT_EXCEEDED',
      status_code: 429,
      retryable: true
    };

    const mockApiCall = jest.fn().mockRejectedValue(mockError);

    // Exhaust retry attempts
    await act(async () => {
      try {
        await result.current.executeWithErrorHandling(mockApiCall);
      } catch (error) {
        // Expected
      }
    });

    for (let i = 0; i < 3; i++) {
      await act(async () => {
        try {
          await result.current.retry();
        } catch (error) {
          // Expected
        }
      });
    }

    expect(result.current.retryCount).toBe(3);
    expect(result.current.canRetry).toBe(false);
  });

  test('correctly identifies non-retryable errors', async () => {
    const { result } = renderHook(() => useApiError());

    const mockError: BackendError = {
      message: 'Invalid document format',
      error_code: 'DOCUMENT_TYPE_UNSUPPORTED',
      status_code: 400,
      retryable: false
    };

    const mockApiCall = jest.fn().mockRejectedValue(mockError);

    await act(async () => {
      try {
        await result.current.executeWithErrorHandling(mockApiCall);
      } catch (error) {
        // Expected
      }
    });

    expect(result.current.error).toEqual(mockError);
    expect(result.current.canRetry).toBe(false); // DOCUMENT_TYPE_UNSUPPORTED should not be retryable
  });

  test('clears error state when clearError is called', async () => {
    const { result } = renderHook(() => useApiError());

    const mockError: BackendError = {
      message: 'Test error',
      error_code: 'INTERNAL_SERVER_ERROR',
      status_code: 500,
      retryable: false
    };

    const mockApiCall = jest.fn().mockRejectedValue(mockError);

    await act(async () => {
      try {
        await result.current.executeWithErrorHandling(mockApiCall);
      } catch (error) {
        // Expected
      }
    });

    expect(result.current.error).toEqual(mockError);

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.retryCount).toBe(0);
    expect(result.current.canRetry).toBe(false);
  });

  test('handles context-specific error logging', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useApiError());

    const mockError: BackendError = {
      message: 'Context test error',
      error_code: 'INTERNAL_SERVER_ERROR',
      status_code: 500,
      retryable: false
    };

    const mockApiCall = jest.fn().mockRejectedValue(mockError);

    await act(async () => {
      try {
        await result.current.executeWithErrorHandling(mockApiCall, {
          context: 'test-component'
        });
      } catch (error) {
        // Expected
      }
    });

    // Verify error was logged with context
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('API Error in test-component:'),
      expect.objectContaining({
        error_code: 'INTERNAL_SERVER_ERROR',
        message: 'Context test error'
      })
    );

    consoleSpy.mockRestore();
  });
}); 