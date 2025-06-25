'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Fade,
  Grow,
} from '@mui/material'
import {
  Send as SendIcon,
  Chat as ChatIcon,
} from '@mui/icons-material'


interface QuickChatInterfaceProps {
  onSendMessage?: (message: string) => void
}

export default function QuickChatInterface({ onSendMessage }: QuickChatInterfaceProps) {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isFocused, setIsFocused] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!message.trim() || isLoading) return

    const userMessage = message.trim()
    setIsLoading(true)

    try {
      // Optional: Send message callback for parent component
      if (onSendMessage) {
        onSendMessage(userMessage)
      }

      // Store the message in sessionStorage so the chat page can pick it up
      sessionStorage.setItem('pendingChatMessage', userMessage)
      
      // Navigate to chat page with smooth transition
      await new Promise(resolve => setTimeout(resolve, 300)) // Small delay for UX
      router.push('/chat')
      
    } catch (error) {
      console.error('Fehler beim Senden der Nachricht:', error)
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as React.FormEvent)
    }
  }

  return (
    <Grow in timeout={1000}>
      <Paper 
        elevation={isFocused ? 8 : 3}
        sx={{ 
          p: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          transition: 'all 0.3s ease-in-out',
          transform: isFocused ? 'translateY(-2px)' : 'translateY(0)',
          '&:hover': {
            elevation: 6,
            transform: 'translateY(-1px)',
          }
        }}
      >
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <ChatIcon color="primary" sx={{ fontSize: 28 }} />
          <Box>
            <Typography variant="h5" fontWeight="600" color="primary.main">
              KI-Assistent
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Stellen Sie Ihre Frage zum Wissenssystem
            </Typography>
          </Box>
        </Box>

        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{
            display: 'flex',
            gap: 1,
            alignItems: 'flex-end'
          }}
        >
          <TextField
            fullWidth
            multiline
            maxRows={3}
            placeholder="Was möchten Sie wissen?"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'background.paper',
                borderRadius: 2,
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                },
                '&.Mui-focused': {
                  backgroundColor: 'background.paper',
                  boxShadow: '0 0 0 2px rgba(25, 118, 210, 0.2)',
                }
              }
            }}
          />
          
          <IconButton
            type="submit"
            disabled={!message.trim() || isLoading}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              width: 48,
              height: 48,
              '&:hover': {
                bgcolor: 'primary.dark',
                transform: 'scale(1.05)',
              },
              '&:disabled': {
                bgcolor: 'action.disabled',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            {isLoading ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <SendIcon />
            )}
          </IconButton>
        </Box>

        <Fade in={message.length > 0} timeout={300}>
          <Typography 
            variant="caption" 
            color="text.secondary" 
            sx={{ 
              mt: 1, 
              display: 'block',
              fontStyle: 'italic' 
            }}
          >
            Drücken Sie Enter oder klicken Sie senden, um zur Chat-Seite zu wechseln
          </Typography>
        </Fade>
      </Paper>
    </Grow>
  )
} 