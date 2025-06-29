'use client'

import { 
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Close as CloseIcon 
} from '@mui/icons-material'
import {
  Snackbar,
  Alert,
  AlertTitle,
  Button,
  Box,
  Typography,
  Collapse,
  IconButton
} from '@mui/material'
import React, { useEffect, useState } from 'react'

import { useGlobalApiError, GlobalApiError } from '@/contexts/ApiErrorContext'

// K3.1.3 Global Error Toast - Non-blocking notifications for system-wide errors
export default function GlobalErrorToast() {
  const { errors, clearError } = useGlobalApiError()
  const [showDetails, setShowDetails] = useState(false)
  const [currentError, setCurrentError] = useState<GlobalApiError | null>(null)

  // Show global/system errors that don't belong to specific components
  useEffect(() => {
    const globalError = errors.global || errors.system || null
    setCurrentError(globalError)
    
    if (globalError) {
      // Auto-dismiss non-critical errors after 10 seconds
      if (globalError.severity !== 'error') {
        const timer = setTimeout(() => {
          clearError(globalError.source)
        }, 10000)
        
        return () => clearTimeout(timer)
      }
    }
  }, [errors, clearError])

  const handleClose = () => {
    if (currentError) {
      clearError(currentError.source)
    }
    setShowDetails(false)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'error'
      case 'warning': return 'warning' 
      case 'info': return 'info'
      default: return 'error'
    }
  }

  const getErrorTitle = (error: GlobalApiError) => {
    switch (error.source) {
      case 'global':
        return 'System-Benachrichtigung'
      case 'system':
        return 'System-Fehler'
      default:
        return 'Benachrichtigung'
    }
  }

  if (!currentError) {
    return null
  }

  return (
    <Snackbar
      open={!!currentError}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      autoHideDuration={currentError.severity === 'error' ? null : 8000}
      sx={{ 
        mt: 2,
        '& .MuiSnackbarContent-root': {
          padding: 0
        }
      }}
    >
      <Alert 
        severity={getSeverityColor(currentError.severity)}
        variant="filled"
        sx={{ 
          minWidth: 400,
          maxWidth: 600
        }}
        action={
          <IconButton
            size="small"
            aria-label="close"
            color="inherit"
            onClick={handleClose}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
      >
        <AlertTitle>{getErrorTitle(currentError)}</AlertTitle>
        
        <Box>
          <Typography variant="body2" component="div">
            {currentError.message}
          </Typography>
          
          {(currentError.error_code || currentError.context || currentError.details) && (
            <Box mt={1}>
              <Button
                size="small"
                color="inherit"
                startIcon={showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                onClick={() => setShowDetails(!showDetails)}
                sx={{ 
                  textTransform: 'none',
                  fontSize: '0.75rem',
                  minHeight: 'auto',
                  p: 0.5
                }}
              >
                {showDetails ? 'Details ausblenden' : 'Details anzeigen'}
              </Button>
              
              <Collapse in={showDetails}>
                <Box mt={1} sx={{ 
                  bgcolor: 'rgba(255,255,255,0.1)', 
                  p: 1, 
                  borderRadius: 1,
                  fontSize: '0.75rem'
                }}>
                  {currentError.error_code && (
                    <Typography variant="caption" display="block">
                      <strong>Fehlercode:</strong> {currentError.error_code}
                    </Typography>
                  )}
                  {currentError.context && (
                    <Typography variant="caption" display="block">
                      <strong>Kontext:</strong> {currentError.context}
                    </Typography>
                  )}
                  {currentError.retryable && (
                    <Typography variant="caption" display="block" color="inherit">
                      <strong>Status:</strong> Fehler kann automatisch behoben werden
                    </Typography>
                  )}
                  <Typography variant="caption" display="block" sx={{ opacity: 0.8 }}>
                    <strong>Zeit:</strong> {new Date(currentError.timestamp).toLocaleTimeString()}
                  </Typography>
                </Box>
              </Collapse>
            </Box>
          )}
          
          {currentError.retryable && currentError.severity === 'error' && (
            <Box mt={1}>
              <Button
                variant="outlined"
                size="small"
                color="inherit"
                onClick={() => {
                  // Trigger retry logic - this would be connected to specific retry mechanisms
                  console.log('Retry requested for error:', currentError.id)
                  handleClose()
                }}
                sx={{ 
                  borderColor: 'rgba(255,255,255,0.5)',
                  color: 'inherit',
                  textTransform: 'none'
                }}
              >
                Erneut versuchen
              </Button>
            </Box>
          )}
        </Box>
      </Alert>
    </Snackbar>
  )
} 