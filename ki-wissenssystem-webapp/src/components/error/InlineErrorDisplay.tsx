'use client'

import {
  ErrorOutline as ErrorIcon,
  WarningAmber as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Typography,
  Collapse,
  Chip,
  Paper
} from '@mui/material'
import React, { useEffect, useState } from 'react'

import { useGlobalApiError } from '@/contexts/ApiErrorContext'

interface InlineErrorDisplayProps {
  source: 'chat' | 'fileUpload' | 'graph' | 'global' | 'system'
  variant?: 'alert' | 'banner' | 'minimal' | 'embedded'
  showRetryButton?: boolean
  onRetry?: () => void
  className?: string
  maxRetryAttempts?: number
}

// K3.1.3 Inline Error Display - Component-specific error display
export default function InlineErrorDisplay({
  source,
  variant = 'alert',
  showRetryButton = true,
  onRetry,
  className,
  maxRetryAttempts = 3
}: InlineErrorDisplayProps) {
  const { getError, clearError, hasRetryableError } = useGlobalApiError()
  const [showDetails, setShowDetails] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  
  const error = getError(source)

  // Reset retry count when error changes
  useEffect(() => {
    setRetryCount(0)
    setShowDetails(false)
  }, [error?.id])

  if (!error) {
    return null
  }

  const handleRetry = () => {
    if (retryCount >= maxRetryAttempts) {
      return
    }
    
    setRetryCount(prev => prev + 1)
    clearError(source)
    
    if (onRetry) {
      onRetry()
    }
  }

  const handleDismiss = () => {
    clearError(source)
    setShowDetails(false)
  }

  const getSourceDisplayName = (source: string) => {
    switch (source) {
      case 'chat': return 'Chat'
      case 'fileUpload': return 'Datei-Upload'
      case 'graph': return 'Knowledge Graph'
      case 'global': return 'System'
      case 'system': return 'System'
      default: return 'Anwendung'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return <ErrorIcon fontSize="small" />
      case 'warning': return <WarningIcon fontSize="small" />
      case 'info': return <InfoIcon fontSize="small" />
      default: return <ErrorIcon fontSize="small" />
    }
  }

  const canRetry = hasRetryableError(source) && showRetryButton && retryCount < maxRetryAttempts

  // Minimal variant - just a small error indicator
  if (variant === 'minimal') {
    return (
      <Chip
        icon={getSeverityIcon(error.severity)}
        label={`Fehler in ${getSourceDisplayName(source)}`}
        color={error.severity === 'error' ? 'error' : 'warning'}
        size="small"
        onClick={() => setShowDetails(!showDetails)}
        className={className}
      />
    )
  }

  // Banner variant - full width, less padding
  if (variant === 'banner') {
    return (
      <Paper
        elevation={0}
        data-testid="error-message"
        sx={{
          bgcolor: error.severity === 'error' ? 'error.light' : 'warning.light',
          color: error.severity === 'error' ? 'error.contrastText' : 'warning.contrastText',
          p: 2,
          mb: 2,
          borderLeft: 4,
          borderColor: error.severity === 'error' ? 'error.main' : 'warning.main'
        }}
        className={className}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            {getSeverityIcon(error.severity)}
            <Typography variant="body2" fontWeight="medium">
              {error.message}
            </Typography>
          </Box>
          
          {canRetry && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRetry}
              sx={{ 
                borderColor: 'currentColor',
                color: 'inherit',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.1)'
                }
              }}
            >
              Wiederholen ({maxRetryAttempts - retryCount} verbleibend)
            </Button>
          )}
        </Box>
      </Paper>
    )
  }

  // Embedded variant - fits into existing UI without margins
  if (variant === 'embedded') {
    return (
      <Box className={className} data-testid="error-message">
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          {getSeverityIcon(error.severity)}
          <Typography 
            variant="body2" 
            color={error.severity === 'error' ? 'error.main' : 'warning.main'}
            fontWeight="medium"
          >
            {error.message}
          </Typography>
        </Box>
        
        {canRetry && (
          <Button
            size="small"
            variant="text"
            startIcon={<RefreshIcon />}
            onClick={handleRetry}
            color={error.severity === 'error' ? 'error' : 'warning'}
            sx={{ textTransform: 'none', fontSize: '0.875rem' }}
          >
            Erneut versuchen ({maxRetryAttempts - retryCount} verbleibend)
          </Button>
        )}
      </Box>
    )
  }

  // Default alert variant - full Alert component
  return (
    <Alert 
      severity={error.severity === 'error' ? 'error' : 'warning'}
      sx={{ mb: 2 }}
      className={className}
      data-testid="error-message"
      action={
        <Box display="flex" gap={1}>
          {canRetry && (
            <Button
              color="inherit"
              size="small"
              onClick={handleRetry}
              startIcon={<RefreshIcon />}
              sx={{ textTransform: 'none' }}
            >
              Wiederholen ({maxRetryAttempts - retryCount})
            </Button>
          )}
          <Button
            color="inherit"
            size="small"
            onClick={handleDismiss}
            sx={{ textTransform: 'none' }}
          >
            Schließen
          </Button>
        </Box>
      }
    >
      <AlertTitle>
        Fehler in {getSourceDisplayName(source)}
      </AlertTitle>
      
      <Typography variant="body2" component="div">
        {error.message}
      </Typography>
      
      {(error.error_code || error.context) && (
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
            {showDetails ? 'Details ausblenden' : 'Technical Details'}
          </Button>
          
          <Collapse in={showDetails}>
            <Box mt={1} sx={{ 
              bgcolor: 'rgba(0,0,0,0.05)', 
              p: 1, 
              borderRadius: 1,
              fontSize: '0.75rem'
            }}>
              {error.error_code && (
                <Typography variant="caption" display="block">
                  <strong>Error Code:</strong> {error.error_code}
                </Typography>
              )}
              {error.context && (
                <Typography variant="caption" display="block">
                  <strong>Context:</strong> {error.context}
                </Typography>
              )}
              <Typography variant="caption" display="block" color="text.secondary">
                <strong>Timestamp:</strong> {new Date(error.timestamp).toLocaleString()}
              </Typography>
              {retryCount > 0 && (
                <Typography variant="caption" display="block" color="text.secondary">
                  <strong>Retry Attempts:</strong> {retryCount}/{maxRetryAttempts}
                </Typography>
              )}
            </Box>
          </Collapse>
        </Box>
      )}
    </Alert>
  )
} 