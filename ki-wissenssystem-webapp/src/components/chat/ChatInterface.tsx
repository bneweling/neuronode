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
  IconButton,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Button,
  Menu,
  MenuItem,
  Slide,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Send as SendIcon,
  Stop as StopIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Chat as ChatIcon,
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  AccountTree as GraphIcon,
} from '@mui/icons-material'
import { getAPIClient } from '@/lib/serviceFactory'
import GraphVisualization from '@/components/graph/GraphVisualization'
import { ExplanationGraph } from '@/components/chat/ExplanationGraph'
import { useChatManager, type Message } from '@/hooks/useChatManager'

export default function ChatInterface() {
  // Chat Management Hook
  const chatManager = useChatManager()
  
  // UI State
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [graphViewOpen, setGraphViewOpen] = useState(false)
  const [hasGraphBeenShown, setHasGraphBeenShown] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null)
  const [selectedChatForMenu, setSelectedChatForMenu] = useState<string | null>(null)
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const sidebarRef = useRef<HTMLDivElement>(null)
  
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // Current chat messages
  const messages = chatManager.currentChat?.messages || []

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Check if message content suggests graph-related information
  const hasGraphRelevantContent = (content: string): boolean => {
    const graphKeywords = [
      'graph', 'knoten', 'verbindung', 'beziehung', 'netzwerk', 
      'visualisierung', 'struktur', 'zusammenhang', 'vernetzung',
      'diagramm', 'topologie', 'hierarchie'
    ]
    return graphKeywords.some(keyword => 
      content.toLowerCase().includes(keyword.toLowerCase())
    )
  }

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading || !chatManager.currentChat) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      role: 'user',
      timestamp: new Date()
    }

    // Add user message to current chat
    chatManager.addMessageToChat(chatManager.currentChatId, userMessage)
    setInputValue('')
    setIsLoading(true)
    setError(null)

    try {
      const apiClient = getAPIClient()
      const response = await apiClient.sendMessage(inputValue.trim())
      
      // Use backend decision first, fallback to keyword analysis
      const backendGraphRelevant = response.metadata?.graph_relevant || false
      const keywordGraphRelevant = hasGraphRelevantContent(response.message || '')
      const hasGraphData = backendGraphRelevant || keywordGraphRelevant
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.message || 'Entschuldigung, ich konnte keine Antwort generieren.',
        role: 'assistant',
        timestamp: new Date(),
        hasGraphData,
        explanationGraph: response.metadata?.explanation_graph as any
      }

      // Add assistant message to current chat
      chatManager.addMessageToChat(chatManager.currentChatId, assistantMessage)

      // Show graph view if response has graph-relevant content
      if (hasGraphData) {
        setGraphViewOpen(true)
        setHasGraphBeenShown(true)
      }

    } catch (error) {
      console.error('Chat-Fehler:', error)
      setError('Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut.')
    } finally {
      setIsLoading(false)
    }
  }, [inputValue, isLoading, chatManager])

  const handleNewChat = () => {
    chatManager.createNewChat()
    setSidebarOpen(false)
  }

  const handleDeleteChat = (chatId: string) => {
    if (chatManager.chatSessions.length === 1) return
    chatManager.deleteChat(chatId)
    handleMenuClose()
  }

  const handleRenameChat = (chatId: string, newName: string) => {
    chatManager.renameChat(chatId, newName)
  }

  const handleSwitchChat = (chatId: string) => {
    chatManager.switchToChat(chatId)
    setSidebarOpen(false)
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, chatId: string) => {
    setMenuAnchor(event.currentTarget)
    setSelectedChatForMenu(chatId)
    event.stopPropagation()
  }

  const handleMenuClose = () => {
    setMenuAnchor(null)
    setSelectedChatForMenu(null)
  }

  // Handle outside click to close sidebar
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarOpen && sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        setSidebarOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [sidebarOpen])

  useEffect(() => {
    scrollToBottom()
  }, [messages.length])

  // Listen for pending messages from Quick Chat
  useEffect(() => {
    const handlePendingMessage = (event: CustomEvent) => {
      const pendingMessage = event.detail.message
      if (pendingMessage && !isLoading && chatManager.currentChat) {
        setInputValue(pendingMessage)
        
        const userMessage: Message = {
          id: Date.now().toString(),
          content: pendingMessage,
          role: 'user',
          timestamp: new Date()
        }

        chatManager.addMessageToChat(chatManager.currentChatId, userMessage)
        setIsLoading(true)
        setError(null)

        const sendPendingMessage = async () => {
          try {
            const apiClient = getAPIClient()
            const response = await apiClient.sendMessage(pendingMessage)
            
            // Use backend decision first, fallback to keyword analysis
            const backendGraphRelevant = response.metadata?.graph_relevant || false
            const keywordGraphRelevant = hasGraphRelevantContent(response.message || '')
            const hasGraphData = backendGraphRelevant || keywordGraphRelevant
            
            const assistantMessage: Message = {
              id: (Date.now() + 1).toString(),
              content: response.message || 'Entschuldigung, ich konnte keine Antwort generieren.',
              role: 'assistant',
              timestamp: new Date(),
              hasGraphData
            }

            chatManager.addMessageToChat(chatManager.currentChatId, assistantMessage)

            if (hasGraphData) {
              setGraphViewOpen(true)
              setHasGraphBeenShown(true)
            }

          } catch (error) {
            console.error('Chat-Fehler:', error)
            setError('Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut.')
          } finally {
            setIsLoading(false)
            setInputValue('')
          }
        }

        sendPendingMessage()
      }
    }

    window.addEventListener('sendPendingMessage', handlePendingMessage as EventListener)
    
    return () => {
      window.removeEventListener('sendPendingMessage', handlePendingMessage as EventListener)
    }
  }, [isLoading, chatManager])

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

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Chat Management Sidebar */}
      <Box
        ref={sidebarRef}
        sx={{
          width: sidebarOpen ? (isMobile ? '280px' : '320px') : '0px',
          transition: 'width 0.3s ease-in-out',
          overflow: 'hidden',
          bgcolor: 'background.paper',
          borderRight: sidebarOpen ? 1 : 0,
          borderColor: 'divider',
          position: 'relative',
          zIndex: 1000,
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
            <Typography variant="h6" fontWeight="600">
              Chat-Verlauf
            </Typography>
          </Box>
          <Button
            fullWidth
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleNewChat}
            sx={{ mb: 2 }}
          >
            Neuer Chat
          </Button>
        </Box>

        <List sx={{ flex: 1, overflow: 'auto' }}>
          {chatManager.chatSessions
            .sort((a, b) => b.lastActivity.getTime() - a.lastActivity.getTime())
            .map((chat) => (
            <ListItem key={chat.id} disablePadding>
              <ListItemButton
                selected={chat.id === chatManager.currentChatId}
                onClick={() => handleSwitchChat(chat.id)}
                sx={{
                  '&.Mui-selected': {
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    }
                  }
                }}
              >
                <ListItemIcon sx={{ color: 'inherit' }}>
                  <ChatIcon />
                </ListItemIcon>
                <ListItemText
                  primary={chat.name}
                  secondary={
                    <Box component="span" sx={{ color: 'inherit', opacity: 0.7 }}>
                      {formatDate(chat.lastActivity)}
                    </Box>
                  }
                />
                <IconButton
                  size="small"
                  onClick={(e) => handleMenuOpen(e, chat.id)}
                  sx={{ color: 'inherit' }}
                >
                  <MoreVertIcon />
                </IconButton>
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Main Chat Area */}
      <Box 
        sx={{ 
          flex: graphViewOpen ? '1 1 50%' : '1 1 100%',
          display: 'flex',
          flexDirection: 'column',
          transition: 'flex 0.5s ease-in-out',
          minWidth: '300px'
        }}
      >
        {/* Chat Header */}
        <Box 
          sx={{ 
            p: 2, 
            borderBottom: 1, 
            borderColor: 'divider',
            bgcolor: 'background.paper',
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}
        >
          <IconButton
            onClick={() => setSidebarOpen(!sidebarOpen)}
            sx={{
              bgcolor: sidebarOpen ? 'primary.main' : 'transparent',
              color: sidebarOpen ? 'primary.contrastText' : 'inherit',
              '&:hover': {
                bgcolor: sidebarOpen ? 'primary.dark' : 'action.hover',
              }
            }}
          >
            <MenuIcon />
          </IconButton>
          
          <Box flex={1}>
            <Typography variant="h6" fontWeight="600">
              {chatManager.currentChat?.name || 'Chat'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {messages.length - 1} Nachrichten
            </Typography>
          </Box>

          {hasGraphBeenShown && (
            <IconButton
              onClick={() => setGraphViewOpen(!graphViewOpen)}
              color={graphViewOpen ? "primary" : "default"}
              sx={{
                bgcolor: graphViewOpen ? 'primary.main' : 'transparent',
                color: graphViewOpen ? 'primary.contrastText' : 'inherit',
                '&:hover': {
                  bgcolor: graphViewOpen ? 'primary.dark' : 'action.hover',
                },
                position: 'relative'
              }}
              title={graphViewOpen ? "Graph-Ansicht schließen" : "Vollständige Graph-Ansicht öffnen"}
            >
              <GraphIcon />
              {/* Indikator für verfügbare Graph-Daten */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 4,
                  right: 4,
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'success.main',
                  animation: graphViewOpen ? 'none' : 'pulse 2s infinite'
                }}
              />
            </IconButton>
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Messages */}
        <Paper
          elevation={0}
          sx={{
            flex: 1,
            overflow: 'auto',
            bgcolor: (theme) => 
              theme.palette.mode === 'dark' 
                ? 'rgba(18, 18, 18, 0.95)' 
                : 'rgba(250, 250, 250, 0.95)',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <List sx={{ flex: 1, p: 2 }}>
            {messages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  display: 'flex',
                  flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                  gap: 2,
                  mb: 2
                }}
              >
                {getMessageAvatar(message.role)}
                <Box
                  sx={{
                    maxWidth: '70%',
                    p: 2.5,
                    borderRadius: message.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                    bgcolor: (theme) => {
                      if (message.role === 'user') {
                        return theme.palette.mode === 'dark' 
                          ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                          : 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)'
                      } else {
                        return theme.palette.mode === 'dark'
                          ? 'rgba(42, 42, 42, 0.95)'
                          : 'rgba(255, 255, 255, 0.95)'
                      }
                    },
                    color: (theme) => {
                      if (message.role === 'user') {
                        return '#ffffff'
                      } else {
                        return theme.palette.mode === 'dark' ? '#ffffff' : '#000000'
                      }
                    },
                    boxShadow: (theme) => 
                      theme.palette.mode === 'dark' 
                        ? '0 4px 12px rgba(0, 0, 0, 0.3)' 
                        : '0 2px 8px rgba(0, 0, 0, 0.1)',
                    border: (theme) => 
                      message.role === 'user' 
                        ? 'none' 
                        : theme.palette.mode === 'dark'
                          ? '1px solid rgba(255, 255, 255, 0.1)'
                          : '1px solid rgba(0, 0, 0, 0.08)',
                    position: 'relative',
                    '&::before': message.role === 'user' ? {
                      content: '""',
                      position: 'absolute',
                      bottom: 0,
                      right: -8,
                      width: 0,
                      height: 0,
                      borderLeft: '8px solid transparent',
                      borderTop: '8px solid',
                      borderTopColor: (theme) => 
                        theme.palette.mode === 'dark' ? '#764ba2' : '#42a5f5'
                    } : {
                      content: '""',
                      position: 'absolute',
                      bottom: 0,
                      left: -8,
                      width: 0,
                      height: 0,
                      borderRight: '8px solid transparent',
                      borderTop: '8px solid',
                      borderTopColor: (theme) => 
                        theme.palette.mode === 'dark' ? 'rgba(42, 42, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)'
                    }
                  }}
                >
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </Typography>
                  
                  {/* Explanation Graph für Assistant-Nachrichten mit Graph-Daten */}
                  {message.role === 'assistant' && message.explanationGraph && (
                    <ExplanationGraph 
                      graphData={message.explanationGraph}
                      height={300}
                      title="📊 Antwort-Erklärung"
                    />
                  )}
                  
                  {/* Graph-Hinweis für weitere Exploration */}
                  {message.role === 'assistant' && message.hasGraphData && !message.explanationGraph && (
                    <Box sx={{ 
                      mt: 2, 
                      p: 2, 
                      backgroundColor: 'rgba(25, 118, 210, 0.08)',
                      borderRadius: 1,
                      border: '1px solid rgba(25, 118, 210, 0.2)'
                    }}>
                      <Typography variant="body2" sx={{ 
                        display: 'flex', 
                        alignItems: 'center',
                        color: 'primary.main'
                      }}>
                        <GraphIcon sx={{ mr: 1, fontSize: '1.2em' }} />
                        💡 Diese Antwort enthält Graph-Daten. Öffnen Sie die Graph-Ansicht für eine detaillierte Visualisierung.
                      </Typography>
                    </Box>
                  )}
                  
                  <Box display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                    <Typography
                      variant="caption"
                      sx={{
                        opacity: 0.7,
                        color: 'inherit'
                      }}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                    {message.hasGraphData && (
                      <Chip
                        icon={<GraphIcon />}
                        label="Graph"
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Box>
                </Box>
              </ListItem>
            ))}
            {isLoading && (
              <ListItem sx={{ justifyContent: 'center' }}>
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ ml: 2 }}>
                  KI antwortet...
                </Typography>
              </ListItem>
            )}
            <div ref={messagesEndRef} />
          </List>
        </Paper>

        {/* Input */}
        <Paper
          elevation={3}
          sx={{
            p: 2,
            display: 'flex',
            gap: 2,
            alignItems: 'flex-end',
            bgcolor: 'background.paper'
          }}
        >
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Nachricht eingeben..."
            disabled={isLoading}
            variant="outlined"
            size="small"
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            sx={{
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'grey.300',
                color: 'grey.500',
              }
            }}
          >
            {isLoading ? <StopIcon /> : <SendIcon />}
          </IconButton>
        </Paper>
      </Box>

      {/* Dynamic Graph View */}
      <Slide direction="left" in={graphViewOpen} mountOnEnter unmountOnExit>
        <Box 
          sx={{ 
            flex: '1 1 50%',
            borderLeft: 1,
            borderColor: 'divider',
            bgcolor: (theme) => 
              theme.palette.mode === 'dark' 
                ? 'rgba(18, 18, 18, 0.95)' 
                : 'rgba(250, 250, 250, 0.95)',
            display: 'flex',
            flexDirection: 'column',
            minWidth: '400px'
          }}
        >
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            <GraphVisualization />
          </Box>
        </Box>
      </Slide>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem
          onClick={() => {
            const newName = prompt('Neuer Name:', 
              chatManager.chatSessions.find(c => c.id === selectedChatForMenu)?.name
            )
            if (newName && selectedChatForMenu) {
              handleRenameChat(selectedChatForMenu, newName)
            }
            handleMenuClose()
          }}
        >
          <ListItemIcon>
            <EditIcon />
          </ListItemIcon>
          <ListItemText>Umbenennen</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (selectedChatForMenu && chatManager.chatSessions.length > 1) {
              handleDeleteChat(selectedChatForMenu)
            }
          }}
          disabled={chatManager.chatSessions.length <= 1}
        >
          <ListItemIcon>
            <DeleteIcon />
          </ListItemIcon>
          <ListItemText>Löschen</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  )
} 