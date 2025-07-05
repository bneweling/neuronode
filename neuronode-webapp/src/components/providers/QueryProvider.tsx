'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ReactNode, useMemo } from 'react'

interface QueryProviderProps {
  children: ReactNode
}

export function QueryProvider({ children }: QueryProviderProps) {
  // Create QueryClient with memoization to prevent recreation on re-renders
  const queryClient = useMemo(() => {
    return new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 5 * 60 * 1000, // 5 Minuten - Daten gelten als fresh
          gcTime: 10 * 60 * 1000,   // 10 Minuten Cache-Zeit (früher cacheTime)
          retry: (failureCount, error) => {
            // Keine Retries bei 4xx Client-Fehlern
            if (error instanceof Error) {
              const message = error.message.toLowerCase()
              if (message.includes('4') && message.includes('http')) {
                return false
              }
            }
            // Maximal 3 Retries für andere Fehler
            return failureCount < 3
          },
          retryDelay: (attemptIndex) => {
            // Exponential backoff: 1s, 2s, 4s
            return Math.min(1000 * 2 ** attemptIndex, 30000)
          },
          refetchOnWindowFocus: false, // Verhindert übermäßige Requests beim Fenster-Fokus
          refetchOnMount: true, // Daten beim Mount neu laden
          refetchOnReconnect: true, // Daten nach Netzwerk-Wiederverbindung neu laden
        },
        mutations: {
          retry: (failureCount, error) => {
            // Keine automatischen Retries für Mutations - zu gefährlich für kritische Operationen
            return false
          },
          onError: (error) => {
            // Globale Mutation-Fehlerbehandlung
            console.error('Mutation Error:', error)
          }
        }
      }
    })
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      
      {/* TanStack Query DevTools - nur in Development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools 
          initialIsOpen={false}
          position="bottom-right"
          toggleButtonProps={{
            style: {
              marginLeft: '5px',
              marginBottom: '5px',
              transform: 'scale(0.8)',
            }
          }}
        />
      )}
    </QueryClientProvider>
  )
} 