'use client'

import { Container, Typography, Card, CardContent, List, ListItem, ListItemText, Box, Button } from '@mui/material'
import { useEffect, useState } from 'react'


interface ErrorInfo {
  message: string
  filename: string
  lineno: number
  colno: number
  error: string | Error | null
  timestamp: string
}

export default function DebugPage() {
  const [errors, setErrors] = useState<ErrorInfo[]>([])
  const [consoleErrors, setConsoleErrors] = useState<string[]>([])

  useEffect(() => {
    // Only initialize in development
    if (process.env.NODE_ENV !== 'development') return

    // Sammle window.onerror events
    const originalOnError = window.onerror
    window.onerror = (message, filename, lineno, colno, error) => {
      setErrors(prev => [...prev, {
        message: String(message),
        filename: String(filename),
        lineno: lineno || 0,
        colno: colno || 0,
        error: error?.stack || error || null,
        timestamp: new Date().toISOString()
      }])
      
      if (originalOnError) {
        return originalOnError(message, filename, lineno, colno, error)
      }
      return false
    }

    // Sammle unhandled promise rejections
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      setErrors(prev => [...prev, {
        message: `Unhandled Promise Rejection: ${event.reason}`,
        filename: 'Promise',
        lineno: 0,
        colno: 0,
        error: event.reason,
        timestamp: new Date().toISOString()
      }])
    }

    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    // Überschreibe console.error um Console-Fehler zu sammeln
    const originalConsoleError = console.error
    console.error = (...args) => {
      setConsoleErrors(prev => [...prev, args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ')])
      originalConsoleError(...args)
    }

    return () => {
      window.onerror = originalOnError
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
      console.error = originalConsoleError
    }
  }, [])

  const clearErrors = () => {
    setErrors([])
    setConsoleErrors([])
  }

  // 🔒 Security: Only available in development
  if (process.env.NODE_ENV !== 'development') {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          Debug Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Debug dashboard is only available in development mode.
        </Typography>
      </Container>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        JavaScript Error Debug Dashboard
      </Typography>
      
      <Box sx={{ mb: 2 }}>
        <Button variant="outlined" onClick={clearErrors} sx={{ mr: 2 }}>
          Clear All Errors
        </Button>
        <Typography variant="body2" color="text.secondary">
          Total Errors: {errors.length + consoleErrors.length}
        </Typography>
      </Box>

      {/* Window Errors */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            JavaScript Runtime Errors ({errors.length})
          </Typography>
          {errors.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No runtime errors detected
            </Typography>
          ) : (
            <List>
              {errors.map((error, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={error.message}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          File: {error.filename}:{error.lineno}:{error.colno}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Time: {error.timestamp}
                        </Typography>
                        {error.error && (
                          <Typography 
                            variant="caption" 
                            component="pre" 
                            sx={{ 
                              fontSize: '0.75rem', 
                              whiteSpace: 'pre-wrap',
                              backgroundColor: 'rgba(255, 0, 0, 0.1)',
                              padding: 1,
                              borderRadius: 1,
                              mt: 1
                            }}
                          >
                            {String(error.error)}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Console Errors */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Console Errors ({consoleErrors.length})
          </Typography>
          {consoleErrors.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No console errors detected
            </Typography>
          ) : (
            <List>
              {consoleErrors.map((error, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Typography 
                        component="pre" 
                        sx={{ 
                          fontSize: '0.85rem', 
                          whiteSpace: 'pre-wrap',
                          backgroundColor: 'rgba(255, 165, 0, 0.1)',
                          padding: 1,
                          borderRadius: 1
                        }}
                      >
                        {error}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Diese Seite sammelt alle JavaScript-Fehler, die auf der Website auftreten.
          Navigieren Sie zu anderen Seiten, um deren Fehler zu sammeln.
        </Typography>
      </Box>
    </Container>
  )
} 