import { useCallback, useRef } from 'react'

/**
 * useDebounce Hook für K3.2 Task 2 - API Call Debouncing
 * 
 * Verhindert eine Flut von API-Calls bei schnellen User-Interaktionen
 * durch Verzögerung der Ausführung um die angegebene Delay-Zeit.
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        callback(...args)
      }, delay)
    },
    [callback, delay]
  ) as T

  return debouncedCallback
} 