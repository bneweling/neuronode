import { Refresh, ExpandMore, ExpandLess, Info } from '@mui/icons-material';
import { Alert, Button, Box, Typography, Collapse, IconButton } from '@mui/material';
import React, { Component, ErrorInfo, ReactNode } from 'react';

// K2 Backend Error Code Mapping based on research
export interface BackendError {
  error_code: string;
  message: string;
  details?: string;
  status_code: number;
  retryable?: boolean;
}

// Error types based on K2 Exception System
export type ErrorSeverity = 'error' | 'warning' | 'info' | 'success';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  maxRetries?: number;
  errorType?: 'retryable' | 'non-retryable' | 'auto-detect';
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  retryCount: number;
  showDetails: boolean;
  backendError?: BackendError;
}

/**
 * K3.1 Enterprise Error Boundary with intelligent error differentiation
 * Integrates K2 Exception System with Material-UI for professional UX
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      retryCount: 0,
      showDetails: false
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Parse backend error if available
    const backendError = ErrorBoundary.parseBackendError(error);
    
    return {
      hasError: true,
      error,
      backendError
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    
    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // Log error with context (research-based structured logging)
    console.error('ErrorBoundary caught error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      retryCount: this.state.retryCount,
      backendError: this.state.backendError
    });
  }

  /**
   * Parse backend error from K2 Exception System
   * Based on research findings from FastAPI error structure
   */
  static parseBackendError(error: Error): BackendError | undefined {
    try {
      // Check if error message contains JSON (typical for API errors)
      const messageMatch = error.message.match(/\{.*\}/);
      if (messageMatch) {
        const errorData = JSON.parse(messageMatch[0]);
        return {
          error_code: errorData.error_code || errorData.error || 'UNKNOWN_ERROR',
          message: errorData.detail || errorData.message || error.message,
          details: errorData.details,
          status_code: errorData.status_code || 500,
          retryable: ErrorBoundary.isRetryableError(errorData.error_code || errorData.error)
        };
      }
    } catch {
      // If parsing fails, treat as generic error
    }
    
    return {
      error_code: 'CLIENT_ERROR',
      message: error.message,
      status_code: 500,
      retryable: false
    };
  }

  /**
   * Intelligent error classification based on K2 Error Codes
   * Research-based mapping from FastAPI documentation
   */
  static isRetryableError(errorCode: string): boolean {
    // LLM Service errors (often retryable)
    if (errorCode.startsWith('LLM_')) {
      return ['LLM_API_QUOTA_EXCEEDED', 'LLM_API_TIMEOUT', 'LLM_SERVICE_UNAVAILABLE'].includes(errorCode);
    }
    
    // Database errors (sometimes retryable)
    if (errorCode.startsWith('NEO4J_') || errorCode.startsWith('DB_')) {
      return ['NEO4J_CONNECTION_FAILED', 'DB_TIMEOUT'].includes(errorCode);
    }
    
    // Document processing errors (usually not retryable)
    if (errorCode.startsWith('DOC_') || errorCode.startsWith('DOCUMENT_')) {
      return false;
    }
    
    // System errors (sometimes retryable)
    if (errorCode.startsWith('SYS_')) {
      return ['SYS_TEMPORARY_FAILURE'].includes(errorCode);
    }
    
    // Default: not retryable
    return false;
  }

  /**
   * Get Material-UI Alert severity based on error type and retryability
   * Research-based UX optimization
   */
  getErrorSeverity(): ErrorSeverity {
    const { backendError } = this.state;
    
    if (!backendError) return 'error';
    
    // Retryable errors are warnings (user can fix)
    if (backendError.retryable) return 'warning';
    
    // Client errors (4xx) are info (user needs to change something)
    if (backendError.status_code >= 400 && backendError.status_code < 500) {
      return 'info';
    }
    
    // Server errors (5xx) are errors (system problem)
    return 'error';
  }

  /**
   * Get human-readable error message
   * Research-based user-friendly messaging
   */
  getHumanReadableMessage(): string {
    const { backendError } = this.state;
    
    if (!backendError) return 'Ein unerwarteter Fehler ist aufgetreten.';
    
    // Specific messages for common K2 error codes
    switch (backendError.error_code) {
      case 'LLM_API_QUOTA_EXCEEDED':
        return 'KI-Service ist überlastet. Automatischer Retry wird durchgeführt...';
      case 'DOCUMENT_TYPE_UNSUPPORTED':
        return 'Dateiformat nicht unterstützt. Bitte wählen Sie eine andere Datei.';
      case 'NEO4J_CONNECTION_FAILED':
        return 'Datenbankverbindung fehlgeschlagen. Bitte versuchen Sie es erneut.';
      case 'EXTRACTION_FAILED':
        return 'Dokument konnte nicht verarbeitet werden. Überprüfen Sie den Dateiinhalt.';
      default:
        return backendError.message || 'Ein Fehler ist aufgetreten.';
    }
  }

  /**
   * Retry mechanism with intelligent limits
   */
  handleRetry = (): void => {
    const maxRetries = this.props.maxRetries || 3;
    
    if (this.state.retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: undefined,
        errorInfo: undefined,
        retryCount: prevState.retryCount + 1,
        showDetails: false
      }));
    }
  };

  /**
   * Toggle error details visibility
   */
  toggleDetails = (): void => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails
    }));
  };

  /**
   * Determine if retry should be shown
   */
  shouldShowRetry(): boolean {
    const { backendError, retryCount } = this.state;
    const maxRetries = this.props.maxRetries || 3;
    
    // Don't show retry if max retries reached
    if (retryCount >= maxRetries) return false;
    
    // For auto-detect mode, use backend error retryable flag
    if (this.props.errorType === 'auto-detect' || !this.props.errorType) {
      return backendError?.retryable || false;
    }
    
    // For explicit modes
    return this.props.errorType === 'retryable';
  }

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    // Use custom fallback if provided
    if (this.props.fallback) {
      return this.props.fallback;
    }

    const severity = this.getErrorSeverity();
    const message = this.getHumanReadableMessage();
    const showRetry = this.shouldShowRetry();
    const { retryCount } = this.state;
    const maxRetries = this.props.maxRetries || 3;

    return (
      <Box sx={{ p: 2 }}>
        <Alert 
          severity={severity}
          action={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {showRetry && (
                <Button
                  color="inherit"
                  size="small"
                  onClick={this.handleRetry}
                  startIcon={<Refresh />}
                  disabled={retryCount >= maxRetries}
                >
                  {retryCount > 0 ? `Retry (${retryCount}/${maxRetries})` : 'Erneut versuchen'}
                </Button>
              )}
              <IconButton
                color="inherit"
                size="small"
                onClick={this.toggleDetails}
                aria-label="Details anzeigen"
              >
                {this.state.showDetails ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>
          }
        >
          <Typography variant="body2" component="div">
            {message}
          </Typography>
          
          {this.state.backendError?.error_code && (
            <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.8 }}>
              Error Code: {this.state.backendError.error_code}
            </Typography>
          )}
          
          <Collapse in={this.state.showDetails}>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0,0,0,0.05)', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                <Info fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Technische Details:
              </Typography>
              
              {this.state.backendError && (
                <Box component="pre" sx={{ fontSize: '0.75rem', overflow: 'auto', maxHeight: 200 }}>
                  {JSON.stringify({
                    error_code: this.state.backendError.error_code,
                    status_code: this.state.backendError.status_code,
                    retryable: this.state.backendError.retryable,
                    details: this.state.backendError.details
                  }, null, 2)}
                </Box>
              )}
              
              {this.state.error && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" display="block">
                    Error: {this.state.error.message}
                  </Typography>
                  {this.state.error.stack && (
                    <Box component="pre" sx={{ fontSize: '0.7rem', overflow: 'auto', maxHeight: 150, mt: 1 }}>
                      {this.state.error.stack.substring(0, 500)}...
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          </Collapse>
        </Alert>
      </Box>
    );
  }
} 