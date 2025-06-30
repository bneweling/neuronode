import { useState, useCallback } from 'react'

export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant' | 'system'
  timestamp: Date
  hasGraphData?: boolean
  explanationGraph?: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      size: number;
      color: string;
      metadata: {
        title: string;
        source: string;
        relevance: number;
        content_preview: string;
      };
    }>;
    edges: Array<{
      source: string;
      target: string;
      label: string;
      weight: number;
      color: string;
    }>;
    layout?: string;
    interactive?: boolean;
  }
}

export interface ChatSession {
  id: string
  name: string
  messages: Message[]
  createdAt: Date
  lastActivity: Date
}

export interface UseChatManagerReturn {
  chatSessions: ChatSession[]
  currentChatId: string
  currentChat: ChatSession | undefined
  createNewChat: () => void
  deleteChat: (chatId: string) => void
  renameChat: (chatId: string, newName: string) => void
  switchToChat: (chatId: string) => void
  addMessageToChat: (chatId: string, message: Message) => void
  updateChatActivity: (chatId: string) => void
}

export const useChatManager = (): UseChatManagerReturn => {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([
    {
      id: '1',
      name: 'Neuer Chat',
      messages: [{
        id: '1',
        content: 'Hallo! Ich bin Ihr KI-Assistent. Wie kann ich Ihnen heute helfen?',
        role: 'assistant',
        timestamp: new Date()
      }],
      createdAt: new Date(),
      lastActivity: new Date()
    }
  ])

  const [currentChatId, setCurrentChatId] = useState('1')

  const currentChat = chatSessions.find(chat => chat.id === currentChatId)

  const createNewChat = useCallback(() => {
    const newChat: ChatSession = {
      id: Date.now().toString(),
      name: `Chat ${chatSessions.length + 1}`,
      messages: [{
        id: Date.now().toString(),
        content: 'Hallo! Ich bin Ihr KI-Assistent. Wie kann ich Ihnen heute helfen?',
        role: 'assistant',
        timestamp: new Date()
      }],
      createdAt: new Date(),
      lastActivity: new Date()
    }
    
    setChatSessions(prev => [...prev, newChat])
    setCurrentChatId(newChat.id)
  }, [chatSessions.length])

  const deleteChat = useCallback((chatId: string) => {
    if (chatSessions.length === 1) return // Don't delete last chat
    
    setChatSessions(prev => prev.filter(chat => chat.id !== chatId))
    
    // Switch to another chat if current was deleted
    if (chatId === currentChatId) {
      const remainingChats = chatSessions.filter(chat => chat.id !== chatId)
      if (remainingChats.length > 0) {
        setCurrentChatId(remainingChats[0].id)
      }
    }
  }, [chatSessions, currentChatId])

  const renameChat = useCallback((chatId: string, newName: string) => {
    setChatSessions(prev => prev.map(chat => 
      chat.id === chatId ? { ...chat, name: newName } : chat
    ))
  }, [])

  const switchToChat = useCallback((chatId: string) => {
    setCurrentChatId(chatId)
  }, [])

  const addMessageToChat = useCallback((chatId: string, message: Message) => {
    setChatSessions(prev => prev.map(chat => 
      chat.id === chatId 
        ? { 
            ...chat, 
            messages: [...chat.messages, message],
            lastActivity: new Date()
          }
        : chat
    ))
  }, [])

  const updateChatActivity = useCallback((chatId: string) => {
    setChatSessions(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, lastActivity: new Date() }
        : chat
    ))
  }, [])

  return {
    chatSessions,
    currentChatId,
    currentChat,
    createNewChat,
    deleteChat,
    renameChat,
    switchToChat,
    addMessageToChat,
    updateChatActivity
  }
} 