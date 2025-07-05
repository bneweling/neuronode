'use client'

import { Box } from '@mui/material'
import { useEffect } from 'react'

import ChatInterface from '@/components/chat/ChatInterface'
import ChatErrorBoundary from '@/components/error/ChatErrorBoundary'
import { PerformanceMonitor } from '@/lib/performance'

export default function ChatPage() {
  useEffect(() => {
    // Performance Monitoring
    PerformanceMonitor.trackPageLoad('ChatPage')
    
    // Check for pending message from Quick Chat
    const pendingMessage = sessionStorage.getItem('pendingChatMessage')
    if (pendingMessage) {
      // Clear the pending message
      sessionStorage.removeItem('pendingChatMessage')
      
      // Trigger sending the message in the ChatInterface
      // This will be handled by the ChatInterface component
      const event = new CustomEvent('sendPendingMessage', {
        detail: { message: pendingMessage }
      })
      window.dispatchEvent(event)
    }
  }, [])

  return (
    <Box sx={{ height: '100vh', overflow: 'hidden' }}>
      <ChatErrorBoundary>
        <ChatInterface />
      </ChatErrorBoundary>
    </Box>
  )
} 