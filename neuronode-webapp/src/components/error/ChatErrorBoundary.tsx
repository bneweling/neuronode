'use client'

import { Alert, AlertTitle, Button, Box } from '@mui/material';
import React from 'react';

interface ChatErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ChatErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export class ChatErrorBoundary extends React.Component<ChatErrorBoundaryProps, ChatErrorBoundaryState> {
  constructor(props: ChatErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ChatErrorBoundaryState {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ChatErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
          <Alert severity="error">
            <AlertTitle>Chat-Komponente Fehler</AlertTitle>
            Ein Fehler ist in der Chat-Komponente aufgetreten.
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                <strong>Fehler:</strong> {this.state.error.message}
                {this.state.error.stack && (
                  <pre style={{ 
                    fontSize: '12px', 
                    overflow: 'auto', 
                    maxHeight: '200px',
                    marginTop: '8px'
                  }}>
                    {this.state.error.stack}
                  </pre>
                )}
              </Box>
            )}
            
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="outlined" 
                onClick={this.handleReset}
                sx={{ mr: 1 }}
              >
                Komponente neu laden
              </Button>
              <Button 
                variant="outlined" 
                onClick={() => window.location.reload()}
              >
                Seite neu laden
              </Button>
            </Box>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ChatErrorBoundary; 