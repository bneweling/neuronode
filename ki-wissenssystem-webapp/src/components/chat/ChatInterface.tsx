'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  TextField,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  Container,
  IconButton,
} from '@mui/material'
import {
  Send as SendIcon,
  Stop as StopIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import { getAPIClient } from '@/lib/api'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant' | 'system'
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hallo! Ich bin Ihr KI-Assistent. Wie kann ich Ihnen heute helfen?',
      role: 'assistant',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setError(null)

    try {
      const apiClient = getAPIClient()
      const response = await apiClient.sendMessage(inputValue.trim())
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.message || 'Entschuldigung, ich konnte keine Antwort generieren.',
        role: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat-Fehler:', error)
      setError('Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut.')
    } finally {
      setIsLoading(false)
    }
  }, [inputValue, isLoading])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Listen for pending messages from Quick Chat and auto-send them
  useEffect(() => {
    const handlePendingMessage = (event: CustomEvent) => {
      const pendingMessage = event.detail.message
      if (pendingMessage && !isLoading) {
        // Set the message in input field
        setInputValue(pendingMessage)
        
        // Create a user message immediately and send it
        const userMessage: Message = {
          id: Date.now().toString(),
          content: pendingMessage,
          role: 'user',
          timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setIsLoading(true)
        setError(null)

        // Send to API
        const sendPendingMessage = async () => {
          try {
            const apiClient = getAPIClient()
            const response = await apiClient.sendMessage(pendingMessage)
            
            const assistantMessage: Message = {
              id: (Date.now() + 1).toString(),
              content: response.message || 'Entschuldigung, ich konnte keine Antwort generieren.',
              role: 'assistant',
              timestamp: new Date()
            }

            setMessages(prev => [...prev, assistantMessage])
          } catch (error) {
            console.error('Chat-Fehler:', error)
            setError('Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut.')
          } finally {
            setIsLoading(false)
            setInputValue('') // Clear input after sending
          }
        }

        sendPendingMessage()
      }
    }

    window.addEventListener('sendPendingMessage', handlePendingMessage as EventListener)
    
    return () => {
      window.removeEventListener('sendPendingMessage', handlePendingMessage as EventListener)
    }
  }, [isLoading])

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  const getMessageAvatar = (role: string) => {
    switch (role) {
      case 'user':
        return (
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <PersonIcon />
          </Avatar>
        )
      case 'assistant':
        return (
          <Avatar sx={{ bgcolor: 'secondary.main' }}>
            <BotIcon />
          </Avatar>
        )
      case 'system':
        return (
          <Avatar sx={{ bgcolor: 'warning.main' }}>
            <SettingsIcon />
          </Avatar>
        )
      default:
        return <Avatar>{role.charAt(0).toUpperCase()}</Avatar>
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          KI-Chat
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Stellen Sie Fragen zu Ihrem Wissenssystem
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Chat Messages */}
      <Paper 
        elevation={1} 
        sx={{ 
          flexGrow: 1, 
          mb: 2, 
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          <List>
            {messages.map((message) => (
              <ListItem 
                key={message.id}
                sx={{
                  flexDirection: 'column',
                  alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    gap: 2,
                    maxWidth: '70%'
                  }}
                >
                  {getMessageAvatar(message.role)}
                  <Box>
                    <Paper
                      elevation={1}
                      sx={{
                        p: 2,
                        bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                        color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                        borderRadius: 2,
                        '&:hover': {
                          elevation: 2
                        }
                      }}
                    >
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                    </Paper>
                    <Typography 
                      variant="caption" 
                      color="text.secondary" 
                      sx={{ 
                        display: 'block', 
                        mt: 0.5,
                        textAlign: message.role === 'user' ? 'right' : 'left'
                      }}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                  </Box>
                </Box>
              </ListItem>
            ))}
            
            {isLoading && (
              <ListItem sx={{ justifyContent: 'flex-start' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  {getMessageAvatar('assistant')}
                  <Paper elevation={1} sx={{ p: 2, borderRadius: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={16} />
                      <Typography variant="body2" color="text.secondary">
                        KI denkt nach...
                      </Typography>
                    </Box>
                  </Paper>
                </Box>
              </ListItem>
            )}
          </List>
          <div ref={messagesEndRef} />
        </Box>
      </Paper>

      {/* Input Area */}
      <Paper elevation={2} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Schreiben Sie Ihre Nachricht..."
            disabled={isLoading}
            variant="outlined"
            size="small"
          />
          <IconButton
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            color="primary"
            size="large"
            sx={{
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': {
                bgcolor: 'primary.dark'
              },
              '&:disabled': {
                bgcolor: 'action.disabled'
              }
            }}
          >
            {isLoading ? <StopIcon /> : <SendIcon />}
          </IconButton>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Drücken Sie Enter zum Senden, Shift+Enter für neue Zeile
          </Typography>
          <Chip 
            label={`${messages.length} Nachrichten`} 
            size="small" 
            variant="outlined" 
          />
        </Box>
      </Paper>
    </Container>
  )
} 