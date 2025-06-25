'use client'

import { useState, useRef, useEffect } from 'react'
import { useWebSocketChat, ChatMessage } from '@/lib/websocket'
import { useMaterialTheme } from '@/lib/theme'

export default function ChatInterface() {
  const { connected, messages, isTyping, sendMessage, clearMessages } = useWebSocketChat()
  const [inputValue, setInputValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { breakpoint } = useMaterialTheme()

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || !connected || isSubmitting) return

    setIsSubmitting(true)
    try {
      await sendMessage(inputValue.trim())
      setInputValue('')
    } catch (error) {
      console.error('Fehler beim Senden der Nachricht:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp)
  }

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user'
    const isSystem = message.type === 'system'

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} ${
          isSystem ? 'justify-center' : ''
        } mb-4`}
      >
        <div
          className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-lg ${
            isUser
              ? 'chat-message-user'
              : isSystem
              ? 'md-surface-variant md-shape-medium text-center'
              : 'chat-message-assistant'
          }`}
        >
          <div className="md-body-large">{message.content}</div>
          
          {/* Sources Display */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 space-y-2">
              <div className="text-xs font-semibold opacity-70">Quellen:</div>
              {message.sources.map((source, index) => (
                <div key={index} className="text-xs opacity-80 md-surface-variant md-shape-small p-2">
                  <div className="font-medium">{source.title}</div>
                  <div className="truncate">{source.content}</div>
                  <div className="text-right opacity-60">Relevanz: {(source.score * 100).toFixed(1)}%</div>
                </div>
              ))}
            </div>
          )}
          
          <div className={`text-xs mt-2 opacity-60 ${isUser ? 'text-right' : 'text-left'}`}>
            {formatTimestamp(message.timestamp)}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-h-screen bg-background">
      {/* Chat Header */}
      <div className="app-header md-elevation-1 p-4 flex items-center justify-between border-b">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
            <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
            </svg>
          </div>
          <div>
            <h2 className="md-headline-large text-lg font-semibold">
              KI-Wissenssystem Chat
            </h2>
            <div className="flex items-center space-x-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}/>
              <span className="opacity-60">
                {connected ? 'Verbunden' : 'Nicht verbunden'}
              </span>
            </div>
          </div>
        </div>
        
        <button
          onClick={clearMessages}
          className="md-surface hover:md-elevation-2 md-shape-medium px-4 py-2 text-sm md-motion-short flex items-center space-x-2"
          disabled={messages.length === 0}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
          </svg>
          <span>Verlauf löschen</span>
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="md-surface md-elevation-2 md-shape-large p-8 text-center max-w-md">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <h3 className="md-headline-large text-lg font-semibold mb-2">
                Willkommen beim KI-Assistenten
              </h3>
              <p className="md-body-large text-gray-600 mb-4">
                Stellen Sie Fragen zu Ihrem Wissenssystem. Der Assistent hilft Ihnen dabei, 
                Informationen zu finden und Zusammenhänge zu erklären.
              </p>
              <div className="text-sm opacity-60 bg-surface-variant rounded-lg p-3">
                <strong>Beispiele:</strong> "Was ist BSI C5?" oder "Zeige mir Compliance-Frameworks"
              </div>
            </div>
          </div>
        )}

        {messages.map(renderMessage)}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start mb-4">
            <div className="chat-message-assistant flex items-center space-x-3 px-4 py-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-sm opacity-70">Assistent antwortet...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 app-header border-t">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={connected ? "Ihre Frage eingeben..." : "Keine Verbindung"}
              disabled={!connected || isSubmitting}
              className="w-full px-4 py-3 md-surface md-shape-large border-2 border-transparent focus:border-primary focus:md-elevation-1 md-motion-short"
              maxLength={1000}
            />
            <div className="absolute right-3 top-3 text-xs opacity-50">
              {inputValue.length}/1000
            </div>
          </div>
          
          <button
            type="submit"
            disabled={!connected || !inputValue.trim() || isSubmitting}
            className="md-primary md-shape-full px-6 py-3 hover:md-elevation-2 md-motion-short disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isSubmitting ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5 fill-white" viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            )}
          </button>
        </form>
        
        {/* Connection Status */}
        {!connected && (
          <div className="mt-3 text-center">
            <span className="text-sm text-red-600 md-surface-variant md-shape-medium px-3 py-2 inline-flex items-center space-x-2">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M1 21h2v-2H1v2zm0-4h2v-2H1v2zm0-4h2v-2H1v2zm0-4h2V7H1v2zm0-4h2V3H1v2zm4 16h2v-2H5v2zm0-8h2v-2H5v2zm0-8h2V3H5v2zm4 16h2v-2H9v2zm0-4h2v-2H9v2zm0-8h2v-2H9v2zm0-8h2V3H9v2zm4 8h2v-2h-2v2zm0-4h2V7h-2v2zm0-4h2V3h-2v2zm4 16h2v-2h-2v2zm0-4h2v-2h-2v2zm0-8h2v-2h-2v2zm0-8h2V3h-2v2zm4 12h2v-2h-2v2zm0-4h2v-2h-2v2zm0-4h2V7h-2v2z"/>
              </svg>
              <span>Verbindung zum Backend unterbrochen</span>
            </span>
          </div>
        )}
      </div>
    </div>
  )
} 