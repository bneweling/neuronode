'use client'

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
  Download as DownloadIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material'
import {
  Box,
  Paper,
  Typography,
  TextField,
  List,
  ListItem,
  Avatar,
  CircularProgress,
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
  Tooltip,
} from '@mui/material'
import { useState, useRef, useEffect, useCallback, useMemo } from 'react'

import GraphVisualization from '@/components/graph/GraphVisualization'
import { useChatApi } from '@/hooks/useChatApi'
import { useChatSearch } from '@/hooks/useChatSearch'
import { getAPIClient } from '@/lib/serviceFactory'
import { 
  useChatStore, 
  useChatActions, 
  useCurrentChat, 
  useAllChats,
  useIsStoreInitialized,
  type Message 
} from '@/stores/chatStore'

function ChatInterfaceCore() {
  // === ENTERPRISE CHAT STORE INTEGRATION ===
  // Replace useChatManager with persistent store
  const currentChat = useCurrentChat()
  const allChats = useAllChats()
  const actions = useChatActions()
  const isStoreInitialized = useIsStoreInitialized()
  const currentChatId = useChatStore((state) => state.currentChatId)
  
  // UI State (kept local as these are ephemeral)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [graphViewOpen, setGraphViewOpen] = useState(false)
  const [hasGraphBeenShown, setHasGraphBeenShown] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null)
  const [selectedChatForMenu, setSelectedChatForMenu] = useState<string | null>(null)
  
  // === CHAT SEARCH INTEGRATION ===
  const {
    searchQuery,
    searchResults,
    searchOptions,
    isSearching,
    searchStats,
    search,
    clearSearch,
    hasResults,
    hasQuery,
    totalMatches,
    searchedChats,
  } = useChatSearch()
  
  // Enhanced Error Handling
  const {
    isLoading,
    executeWithErrorHandling,
    clearError
  } = useChatApi({
    onError: (backendError) => {
      console.error('Chat API Error:', backendError)
    },
    onSuccess: () => {
      console.log('Chat message sent successfully')
    }
  })
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // === INITIALIZATION ===
  // Create initial chat if store is empty - use stable selector
  const chatCount = useChatStore((state) => Object.keys(state.sessions).length)
  
  useEffect(() => {
    if (isStoreInitialized && chatCount === 0) {
      console.log('Creating initial chat session...')
      actions.createNewChat('Willkommen')
    }
  }, [isStoreInitialized, chatCount, actions])

  // Get current messages from store
  const messages = currentChat?.messages || []

  // Memoized sorted chats list - only recalculates when sessions change
  const sortedChats = useMemo(() => {
    return allChats.sort((a, b) => b.lastActivity.getTime() - a.lastActivity.getTime())
  }, [allChats])

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

  // === STABLE MESSAGE SENDING ===
  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading || !currentChatId) return

    const messageContent = inputValue.trim()
    setInputValue('') // Clear input immediately for better UX
    
    // Create user message
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content: messageContent,
      role: 'user',
      timestamp: new Date()
    }

    // Add user message to store
    actions.addMessage(currentChatId, userMessage)
    
    // Clear any existing errors
    clearError()

    try {
      // Enhanced API call with intelligent error handling
      const response = await executeWithErrorHandling(
        async () => {
          const apiClient = getAPIClient()
          return await apiClient.sendMessage(messageContent)
        },
        {
          retryable: true,
          context: 'chat-message'
        }
      )

      // Handle successful response
      if (response) {
        const backendGraphRelevant = response.metadata?.graph_relevant || false
        const keywordGraphRelevant = hasGraphRelevantContent(response.message || '')
        const hasGraphData: boolean = Boolean(backendGraphRelevant || keywordGraphRelevant)
        
        const assistantMessage: Message = {
          id: `assistant_${Date.now()}`,
          content: response.message || 'Entschuldigung, ich konnte keine Antwort generieren.',
          role: 'assistant',
          timestamp: new Date(),
          hasGraphData,
          explanationGraph: response.metadata?.explanation_graph as Message['explanationGraph'],
          metadata: {
            tokens_used: response.metadata?.tokens_used as number | undefined,
            response_time: response.metadata?.response_time as number | undefined,
            model_used: response.metadata?.model_used as string | undefined,
            graph_relevant: Boolean(backendGraphRelevant)
          }
        }

        // Add assistant message to store
        actions.addMessage(currentChatId, assistantMessage)

        // Show graph view if response has graph-relevant content
        if (hasGraphData) {
          setGraphViewOpen(true)
          setHasGraphBeenShown(true)
        }
      }
    } catch (error) {
      console.warn('Chat message sending completed with potential errors:', error)
    }
  }, [inputValue, isLoading, currentChatId, actions, executeWithErrorHandling, clearError])

  // === CHAT MANAGEMENT ACTIONS ===
  const handleNewChat = () => {
    const newChatId = actions.createNewChat(`Chat ${chatCount + 1}`)
    setSidebarOpen(false)
    console.log('Created new chat:', newChatId)
  }

  const handleDeleteChat = (chatId: string) => {
    if (chatCount === 1) return
    actions.deleteChat(chatId)
    handleMenuClose()
  }

  const handleRenameChat = (chatId: string, newName: string) => {
    actions.renameChat(chatId, newName)
  }

  const handleSwitchChat = (chatId: string) => {
    actions.switchChat(chatId)
    setSidebarOpen(false)
  }

  const handleExportChat = (chatId: string) => {
    const exportData = actions.exportChat(chatId)
    if (exportData) {
      const blob = new Blob([exportData], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `chat-export-${chatId}-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
    handleMenuClose()
  }

  const handleImportChat = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const data = e.target?.result as string
      if (actions.importChat(data)) {
        console.log('Chat imported successfully')
      } else {
        console.error('Failed to import chat')
      }
    }
    reader.readAsText(file)
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // === MENU HANDLERS ===
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, chatId: string) => {
    setMenuAnchor(event.currentTarget)
    setSelectedChatForMenu(chatId)
    event.stopPropagation()
  }

  const handleMenuClose = () => {
    setMenuAnchor(null)
    setSelectedChatForMenu(null)
  }

  // === EFFECTS ===
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

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages.length])

  // Listen for pending messages from Quick Chat
  useEffect(() => {
    const handlePendingMessage = (event: CustomEvent) => {
      const pendingMessage = event.detail.message
      if (pendingMessage && !isLoading && currentChatId) {
        setInputValue(pendingMessage)
        
        const userMessage: Message = {
          id: `pending_${Date.now()}`,
          content: pendingMessage,
          role: 'user',
          timestamp: new Date()
        }

        actions.addMessage(currentChatId, userMessage)
        clearError()

        const sendPendingMessage = async () => {
          const response = await executeWithErrorHandling(
            async () => {
              const apiClient = getAPIClient()
              return await apiClient.sendMessage(pendingMessage)
            },
            {
              retryable: true,
              context: 'pending-chat-message'
            }
          )

          if (response) {
            const backendGraphRelevant = response.metadata?.graph_relevant || false
            const keywordGraphRelevant = hasGraphRelevantContent(response.message || '')
            const hasGraphData: boolean = Boolean(backendGraphRelevant || keywordGraphRelevant)
            
            const assistantMessage: Message = {
              id: `pending_assistant_${Date.now()}`,
              content: response.message || 'Entschuldigung, ich konnte keine Antwort generieren.',
              role: 'assistant',
              timestamp: new Date(),
              hasGraphData,
              metadata: {
                graph_relevant: Boolean(backendGraphRelevant)
              }
            }

            actions.addMessage(currentChatId, assistantMessage)

            if (hasGraphData) {
              setGraphViewOpen(true)
              setHasGraphBeenShown(true)
            }
          }
          
          setInputValue('')
        }

        sendPendingMessage()
      }
    }

    window.addEventListener('sendPendingMessage', handlePendingMessage as EventListener)
    
    return () => {
      window.removeEventListener('sendPendingMessage', handlePendingMessage as EventListener)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, currentChatId, executeWithErrorHandling, clearError])

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  // === UI HELPER FUNCTIONS ===
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

  // === LOADING STATE ===
  if (!isStoreInitialized) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh' 
        }}
      >
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Chat wird initialisiert...</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }} data-testid="chat-container">
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
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6" fontWeight="600">
              Chat-Verlauf
            </Typography>
            <Tooltip title="Chat importieren">
              <IconButton
                size="small"
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadIcon />
              </IconButton>
            </Tooltip>
          </Box>
          
          {/* Enhanced Chat Search */}
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Chats durchsuchen..."
              value={searchQuery}
              onChange={(e) => search(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: hasQuery && (
                  <IconButton
                    size="small"
                    onClick={clearSearch}
                    sx={{ mr: -0.5 }}
                  >
                    <ClearIcon />
                  </IconButton>
                )
              }}
              sx={{ mb: 1 }}
            />
            
            {/* Search Stats & Options */}
            {hasQuery && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {isSearching ? 'Suche...' : `${totalMatches} Treffer in ${searchedChats} Chats${searchStats.searchTime > 0 ? ` (${searchStats.searchTime}ms)` : ''}`}
                </Typography>
                {searchOptions.caseSensitive || searchOptions.wholeWords || !searchOptions.searchInMetadata ? (
                  <Typography variant="caption" color="primary" sx={{ ml: 1 }}>
                    • Filter aktiv
                  </Typography>
                ) : null}
              </Box>
            )}
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
          <Typography variant="caption" color="text.secondary">
            {allChats.length} gespeicherte Chats
          </Typography>
        </Box>

        <List sx={{ flex: 1, overflow: 'auto' }}>
          {/* Show search results if searching, otherwise show all chats */}
          {hasQuery && hasResults ? (
            // Search Results
            searchResults.map((result) => (
              <ListItem key={result.chat.id} disablePadding>
                <ListItemButton
                  selected={result.chat.id === currentChatId}
                  onClick={() => handleSwitchChat(result.chat.id)}
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
                    primary={
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {result.chat.title}
                        </Typography>
                        <Typography variant="caption" color="primary" sx={{ bgcolor: 'primary.light', px: 0.5, borderRadius: 0.5 }}>
                          {result.matchingMessages.length} Treffer • Relevanz: {result.relevanceScore}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box component="span" sx={{ color: 'inherit', opacity: 0.7 }}>
                        <Typography variant="caption" component="span" sx={{ display: 'block' }}>
                          {formatDate(result.chat.lastActivity)}
                        </Typography>
                        {result.matchingMessages.slice(0, 2).map((match, index) => (
                          <Typography 
                            key={index}
                            variant="caption" 
                            component="span"
                            sx={{ 
                              display: 'block',
                              fontStyle: 'italic',
                              textOverflow: 'ellipsis',
                              overflow: 'hidden',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            "                            &quot;...{match.context.slice(0, 40)}...&quot;"
                          </Typography>
                        ))}
                      </Box>
                    }
                  />
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, result.chat.id)}
                    sx={{ color: 'inherit' }}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </ListItemButton>
              </ListItem>
            ))
          ) : hasQuery && !hasResults ? (
            // No search results
            <ListItem>
              <ListItemText
                primary={
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <SearchIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      Keine Treffer für &quot;{searchQuery}&quot;
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Versuchen Sie andere Suchbegriffe
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          ) : (
            // All chats (normal view) - use memoized sorted list
            sortedChats.map((chat) => (
              <ListItem key={chat.id} disablePadding>
                <ListItemButton
                  selected={chat.id === currentChatId}
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
                    primary={chat.title}
                    secondary={
                      <Box component="span" sx={{ color: 'inherit', opacity: 0.7 }}>
                        <Typography variant="caption" component="span" sx={{ display: 'block' }}>
                          {formatDate(chat.lastActivity)}
                        </Typography>
                        <Typography variant="caption" component="span" sx={{ display: 'block' }}>
                          {chat.messages.length - 1} Nachrichten
                        </Typography>
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
            ))
          )}
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
              {currentChat?.title || 'Chat'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {messages.length - 1} Nachrichten • Persistent gespeichert
            </Typography>
          </Box>

          {hasGraphBeenShown && (
            <Tooltip title={graphViewOpen ? 'Graph ausblenden' : 'Graph anzeigen'}>
              <IconButton
                onClick={() => setGraphViewOpen(!graphViewOpen)}
                sx={{
                  bgcolor: graphViewOpen ? 'primary.main' : 'transparent',
                  color: graphViewOpen ? 'primary.contrastText' : 'inherit',
                }}
              >
                <IconButton />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Messages Area */}
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
                  data-testid={message.role === 'assistant' ? 'chat-response' : undefined}
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
                  }}
                >
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}
                  >
                    {message.content}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        opacity: 0.7,
                        fontSize: '0.75rem'
                      }}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                    
                    {message.hasGraphData && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="caption" sx={{ opacity: 0.7 }}>
                          Graph verfügbar
                        </Typography>
                      </Box>
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
            placeholder="Nachricht eingeben... (Alle Nachrichten werden automatisch gespeichert)"
            disabled={isLoading}
            variant="outlined"
            size="small"
            data-testid="chat-input"
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            data-testid="chat-send"
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
            const sessions = useChatStore.getState().sessions
            const newName = prompt('Neuer Name:', 
              sessions[selectedChatForMenu || '']?.title
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
            if (selectedChatForMenu) {
              handleExportChat(selectedChatForMenu)
            }
          }}
        >
          <ListItemIcon>
            <DownloadIcon />
          </ListItemIcon>
          <ListItemText>Exportieren</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (selectedChatForMenu && chatCount > 1) {
              handleDeleteChat(selectedChatForMenu)
            }
          }}
          disabled={chatCount <= 1}
        >
          <ListItemIcon>
            <DeleteIcon />
          </ListItemIcon>
          <ListItemText>Löschen</ListItemText>
        </MenuItem>
      </Menu>

      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        style={{ display: 'none' }}
        onChange={handleImportChat}
      />
    </Box>
  )
}

/**
 * Enterprise ChatInterface with Persistent State Management
 * 
 * Features:
 * - Full chat persistence with localStorage
 * - Import/Export functionality
 * - Enhanced metadata tracking
 * - Stable state management
 * - StrictMode compliance
 */
export default function ChatInterface() {
  return <ChatInterfaceCore />
} 