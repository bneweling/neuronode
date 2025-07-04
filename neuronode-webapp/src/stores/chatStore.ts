import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Import data validation interface
interface ImportData {
  version: string
  chat: ChatSession
  exportedAt: string
}

// Validation error types
export interface ValidationError {
  field: string
  message: string
  value?: unknown
}

// Enhanced Message interface with enterprise features
export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant' | 'system'
  timestamp: Date
  hasGraphData?: boolean
  explanationGraph?: {
    nodes: Array<{
      id: string
      label: string
      type: string
      size: number
      color: string
      metadata: {
        title: string
        source: string
        relevance: number
        content_preview: string
      }
    }>
    edges: Array<{
      source: string
      target: string
      label: string
      weight: number
      color: string
    }>
    layout?: string
    interactive?: boolean
  }
  metadata?: {
    tokens_used?: number
    response_time?: number
    model_used?: string
    graph_relevant?: boolean
  }
}

// Enhanced ChatSession interface
export interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  lastActivity: Date
  metadata?: {
    total_messages: number
    total_tokens?: number
    topics?: string[]
    has_graph_data: boolean
  }
}

// Store state interface
interface ChatState {
  sessions: Record<string, ChatSession>
  currentChatId: string | null
  isInitialized: boolean
  
  // Actions
  actions: {
    addMessage: (chatId: string, message: Message) => void
    createNewChat: (title?: string) => string
    switchChat: (chatId: string) => void
    deleteChat: (chatId: string) => void
    renameChat: (chatId: string, newTitle: string) => void
    getChatHistory: (chatId: string) => Message[]
    getAllChats: () => ChatSession[]
    getCurrentChat: () => ChatSession | null
    updateChatMetadata: (chatId: string, metadata: Partial<ChatSession['metadata']>) => void
    clearAllChats: () => void
    exportChat: (chatId: string) => string
    importChat: (data: string) => boolean
  }
}

// === SCHEMA VALIDATION FUNCTIONS ===

/**
 * Validates if an object is a valid Message
 */
const validateMessage = (data: unknown): data is Message => {
  if (!data || typeof data !== 'object') return false
  
  // Cast to any for runtime validation
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const obj = data as any
  
  // Required fields
  if (typeof obj.id !== 'string' || !obj.id.trim()) return false
  if (typeof obj.content !== 'string') return false
  if (!['user', 'assistant', 'system'].includes(obj.role)) return false
  
  // Timestamp validation - can be string (from JSON) or Date
  const timestamp = obj.timestamp
  if (!timestamp) return false
  if (typeof timestamp === 'string') {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return false
  } else if (!(timestamp instanceof Date)) {
    return false
  }
  
  // Optional fields validation
  if (obj.hasGraphData !== undefined && typeof obj.hasGraphData !== 'boolean') return false
  if (obj.explanationGraph !== undefined && typeof obj.explanationGraph !== 'object') return false
  if (obj.metadata !== undefined && typeof obj.metadata !== 'object') return false
  
  return true
}

/**
 * Validates if an object is a valid ChatSession
 */
const validateChatSession = (data: unknown): data is ChatSession => {
  if (!data || typeof data !== 'object') return false
  
  // Cast to any for runtime validation
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const obj = data as any
  
  // Required fields
  if (typeof obj.id !== 'string' || !obj.id.trim()) return false
  if (typeof obj.title !== 'string' || !obj.title.trim()) return false
  if (!Array.isArray(obj.messages)) return false
  
  // Validate all messages
  for (const message of obj.messages) {
    if (!validateMessage(message)) return false
  }
  
  // Date validation - can be string (from JSON) or Date
  const createdAt = obj.createdAt
  const lastActivity = obj.lastActivity
  
  if (!createdAt) return false
  if (typeof createdAt === 'string') {
    const date = new Date(createdAt)
    if (isNaN(date.getTime())) return false
  } else if (!(createdAt instanceof Date)) {
    return false
  }
  
  if (!lastActivity) return false
  if (typeof lastActivity === 'string') {
    const date = new Date(lastActivity)
    if (isNaN(date.getTime())) return false
  } else if (!(lastActivity instanceof Date)) {
    return false
  }
  
  // Optional metadata validation
  if (obj.metadata !== undefined) {
    if (typeof obj.metadata !== 'object') return false
    const meta = obj.metadata
    if (meta.total_messages !== undefined && typeof meta.total_messages !== 'number') return false
    if (meta.total_tokens !== undefined && typeof meta.total_tokens !== 'number') return false
    if (meta.topics !== undefined && !Array.isArray(meta.topics)) return false
    if (meta.has_graph_data !== undefined && typeof meta.has_graph_data !== 'boolean') return false
  }
  
  return true
}

/**
 * Validates if an object is valid import data
 */
const validateImportData = (data: unknown): data is ImportData => {
  if (!data || typeof data !== 'object') return false
  
  // Cast to any for runtime validation
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const obj = data as any
  
  // Version validation
  if (typeof obj.version !== 'string' || !obj.version.trim()) return false
  
  // Export timestamp validation
  if (typeof obj.exportedAt !== 'string') return false
  const exportDate = new Date(obj.exportedAt)
  if (isNaN(exportDate.getTime())) return false
  
  // Chat validation
  if (!obj.chat || !validateChatSession(obj.chat)) return false
  
  return true
}

/**
 * Sanitizes and normalizes import data
 */
const sanitizeImportData = (data: ImportData): ChatSession => {
  const chat = data.chat
  
  // Convert string dates to Date objects
  const sanitizedChat: ChatSession = {
    ...chat,
    id: chat.id,
    title: chat.title.trim(),
    createdAt: typeof chat.createdAt === 'string' ? new Date(chat.createdAt) : chat.createdAt,
    lastActivity: typeof chat.lastActivity === 'string' ? new Date(chat.lastActivity) : chat.lastActivity,
    messages: chat.messages.map(message => ({
      ...message,
      content: message.content.trim(),
      timestamp: typeof message.timestamp === 'string' ? new Date(message.timestamp) : message.timestamp
    }))
  }
  
  return sanitizedChat
}

/**
 * Generates detailed validation errors for debugging
 */
const getValidationErrors = (data: unknown): ValidationError[] => {
  const errors: ValidationError[] = []
  
  if (!data || typeof data !== 'object') {
    errors.push({ field: 'root', message: 'Data must be an object' })
    return errors
  }
  
  // Cast to any for runtime validation
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const obj = data as any
  
  if (typeof obj.version !== 'string' || !obj.version.trim()) {
    errors.push({ field: 'version', message: 'Version must be a non-empty string', value: obj.version })
  }
  
  if (typeof obj.exportedAt !== 'string') {
    errors.push({ field: 'exportedAt', message: 'ExportedAt must be a string', value: obj.exportedAt })
  } else {
    const exportDate = new Date(obj.exportedAt)
    if (isNaN(exportDate.getTime())) {
      errors.push({ field: 'exportedAt', message: 'ExportedAt must be a valid date string', value: obj.exportedAt })
    }
  }
  
  if (!obj.chat) {
    errors.push({ field: 'chat', message: 'Chat data is required' })
  } else if (!validateChatSession(obj.chat)) {
    errors.push({ field: 'chat', message: 'Chat data structure is invalid' })
  }
  
  return errors
}

// Default welcome message
const createWelcomeMessage = (): Message => ({
  id: `welcome_${Date.now()}`,
  content: 'Hallo! Ich bin Ihr KI-Assistent für das Neuronode-Wissenssystem. Ich kann Ihnen bei der Analyse von Dokumenten, der Erkundung des Wissensgraphen und der Beantwortung von Fragen helfen. Wie kann ich Ihnen heute behilflich sein?',
  role: 'assistant',
  timestamp: new Date(),
  hasGraphData: false,
  metadata: {
    model_used: 'system',
    graph_relevant: false
  }
})

// Create default chat session
const createDefaultChat = (): ChatSession => ({
  id: `chat_${Date.now()}`,
  title: 'Neuer Chat',
  messages: [createWelcomeMessage()],
  createdAt: new Date(),
  lastActivity: new Date(),
  metadata: {
    total_messages: 1,
    has_graph_data: false,
    topics: []
  }
})

// Enterprise Chat Store with full persistence
export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: {},
      currentChatId: null,
      isInitialized: false,

      actions: {
        addMessage: (chatId, message) => {
          const state = get()
          const session = state.sessions[chatId]
          
          if (!session) {
            console.warn(`Chat session ${chatId} not found`)
            return
          }

          const updatedMessages = [...session.messages, message]
          const hasGraphData = session.metadata?.has_graph_data || message.hasGraphData || false
          
          set((state) => ({
            sessions: {
              ...state.sessions,
              [chatId]: {
                ...session,
                messages: updatedMessages,
                lastActivity: new Date(),
                metadata: {
                  // Ensure all required fields are properly maintained
                  total_messages: updatedMessages.length,
                  has_graph_data: hasGraphData,
                  // Optional fields from existing metadata (safe to maintain)
                  total_tokens: (session.metadata?.total_tokens || 0) + (message.metadata?.tokens_used || 0),
                  topics: session.metadata?.topics
                }
              }
            }
          }))
        },

        createNewChat: (title?: string) => {
          const newChat = createDefaultChat()
          if (title) {
            newChat.title = title
          }
          
          set((state) => ({
            sessions: { ...state.sessions, [newChat.id]: newChat },
            currentChatId: newChat.id
          }))
          
          return newChat.id
        },

        switchChat: (chatId) => {
          const state = get()
          if (state.sessions[chatId]) {
            set({ currentChatId: chatId })
          } else {
            console.warn(`Chat ${chatId} not found`)
          }
        },

        deleteChat: (chatId) => {
          const state = get()
          const sessions = { ...state.sessions }
          
          // Don't delete if it's the only chat
          if (Object.keys(sessions).length <= 1) {
            return
          }
          
          delete sessions[chatId]
          
          // If we're deleting the current chat, switch to another one
          let newCurrentChatId = state.currentChatId
          if (state.currentChatId === chatId) {
            const remainingChatIds = Object.keys(sessions)
            newCurrentChatId = remainingChatIds.length > 0 ? remainingChatIds[0] : null
          }
          
          set({
            sessions,
            currentChatId: newCurrentChatId
          })
        },

        renameChat: (chatId, newTitle) => {
          const state = get()
          const session = state.sessions[chatId]
          
          if (session) {
            set((state) => ({
              sessions: {
                ...state.sessions,
                [chatId]: {
                  ...session,
                  title: newTitle,
                  lastActivity: new Date()
                }
              }
            }))
          }
        },

        getChatHistory: (chatId) => {
          const state = get()
          return state.sessions[chatId]?.messages || []
        },

        getAllChats: () => {
          const state = get()
          return Object.values(state.sessions).sort(
            (a, b) => b.lastActivity.getTime() - a.lastActivity.getTime()
          )
        },

        getCurrentChat: () => {
          const state = get()
          return state.currentChatId ? state.sessions[state.currentChatId] || null : null
        },

        updateChatMetadata: (chatId, metadata) => {
          const state = get()
          const session = state.sessions[chatId]
          
          if (session) {
            set((state) => ({
              sessions: {
                ...state.sessions,
                [chatId]: {
                  ...session,
                  metadata: {
                    // Ensure all required fields are maintained
                    total_messages: session.metadata?.total_messages || session.messages.length,
                    has_graph_data: session.metadata?.has_graph_data || false,
                    // Merge optional fields from existing metadata and updates
                    total_tokens: metadata?.total_tokens ?? session.metadata?.total_tokens,
                    topics: metadata?.topics ?? session.metadata?.topics
                  },
                  lastActivity: new Date()
                }
              }
            }))
          }
        },

        clearAllChats: () => {
          const defaultChat = createDefaultChat()
          set({
            sessions: { [defaultChat.id]: defaultChat },
            currentChatId: defaultChat.id
          })
        },

        exportChat: (chatId) => {
          const state = get()
          const session = state.sessions[chatId]
          
          if (session) {
            return JSON.stringify({
              version: '1.0',
              chat: session,
              exportedAt: new Date().toISOString()
            }, null, 2)
          }
          
          return ''
        },

        importChat: (data) => {
          try {
            // Parse JSON data
            const parsed = JSON.parse(data)
            
            // Comprehensive validation
            if (!validateImportData(parsed)) {
              const errors = getValidationErrors(parsed)
              console.error('Import validation failed:', {
                errors,
                receivedData: parsed
              })
              
              // User-friendly error reporting
              const errorMessages = errors.map(e => `${e.field}: ${e.message}`).join(', ')
              console.warn(`Chat import failed due to validation errors: ${errorMessages}`)
              
              return false
            }
            
            // Sanitize and normalize data
            const sanitizedChat = sanitizeImportData(parsed)
            
            // Generate new ID to avoid conflicts
            const newId = `imported_${Date.now()}`
            const importedChat: ChatSession = {
              ...sanitizedChat,
              id: newId,
              title: `${sanitizedChat.title} (Importiert)`,
              lastActivity: new Date(),
              metadata: {
                // Ensure all required fields are properly initialized
                total_messages: sanitizedChat.messages.length,
                has_graph_data: sanitizedChat.messages.some(m => m.hasGraphData) || false,
                // Optional fields from the original metadata (safe to spread)
                total_tokens: sanitizedChat.metadata?.total_tokens,
                topics: sanitizedChat.metadata?.topics
              }
            }
            
            // Additional validation: ensure messages have valid structure
            const validMessages = importedChat.messages.filter(message => validateMessage(message))
            if (validMessages.length !== importedChat.messages.length) {
              console.warn(`Import: Filtered out ${importedChat.messages.length - validMessages.length} invalid messages`)
              importedChat.messages = validMessages
              importedChat.metadata!.total_messages = validMessages.length
            }
            
            // Validate final chat structure
            if (!validateChatSession(importedChat)) {
              console.error('Final chat validation failed after sanitization')
              return false
            }
            
            set((state) => ({
              sessions: { ...state.sessions, [newId]: importedChat }
            }))
            
            console.log(`Successfully imported chat "${importedChat.title}" with ${importedChat.messages.length} messages`)
            return true
            
          } catch (error) {
            if (error instanceof SyntaxError) {
              console.error('Import failed: Invalid JSON format', error.message)
            } else {
              console.error('Import failed: Unexpected error', error)
            }
            
            return false
          }
        }
      }
    }),
    {
      name: 'neuronode-chat-storage', // localStorage key
      partialize: (state) => ({
        sessions: state.sessions,
        currentChatId: state.currentChatId
      }),
      onRehydrateStorage: () => (state) => {
        // Initialize with default chat if no sessions exist
        if (state && Object.keys(state.sessions).length === 0) {
          const defaultChat = createDefaultChat()
          state.sessions = { [defaultChat.id]: defaultChat }
          state.currentChatId = defaultChat.id
        }
        
        // Convert timestamp strings back to Date objects (persist serialization)
        if (state) {
          Object.values(state.sessions).forEach(session => {
            session.createdAt = new Date(session.createdAt)
            session.lastActivity = new Date(session.lastActivity)
            session.messages.forEach(message => {
              message.timestamp = new Date(message.timestamp)
            })
          })
          
          state.isInitialized = true
        }
      },
      // Prevent hydration mismatches
      skipHydration: false,
      version: 1
    }
      )
  )

// Enhanced hook for chat store actions
export const useChatActions = () => useChatStore((state) => state.actions)

// Cache for sorted chats to prevent unnecessary re-renders
let sortedChatsCache: ChatSession[] | null = null
let lastSessionsHash: string | null = null

// Optimized selector hooks that prevent infinite re-renders
export const useCurrentChat = (): ChatSession | null => {
  return useChatStore((state) => {
    return state.currentChatId ? state.sessions[state.currentChatId] || null : null
  })
}

export const useAllChats = (): ChatSession[] => {
  return useChatStore((state) => {
    // Create a hash of the sessions to detect changes
    const sessionIds = Object.keys(state.sessions).sort()
    const currentHash = sessionIds.join(',') + JSON.stringify(sessionIds.map(id => state.sessions[id].lastActivity.getTime()))
    
    // Only recalculate if sessions have actually changed
    if (lastSessionsHash !== currentHash || !sortedChatsCache) {
      const sessions = Object.values(state.sessions)
      sortedChatsCache = sessions.sort((a, b) => b.lastActivity.getTime() - a.lastActivity.getTime())
      lastSessionsHash = currentHash
    }
    
    return sortedChatsCache
  })
}

export const useChatHistory = (chatId: string): Message[] => {
  return useChatStore((state) => {
    // Return messages directly instead of calling action function
    return state.sessions[chatId]?.messages || []
  })
}

export const useIsStoreInitialized = () => useChatStore((state) => state.isInitialized) 