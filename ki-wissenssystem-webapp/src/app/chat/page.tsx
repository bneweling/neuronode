'use client'

import { useEffect } from 'react'
import ChatInterface from '@/components/chat/ChatInterface'

export default function ChatPage() {
  useEffect(() => {
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

  return <ChatInterface />
} 