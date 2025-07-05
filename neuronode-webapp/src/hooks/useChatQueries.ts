'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useApiClient } from '@/contexts/ApiClientContext'
import { ChatMessage, ChatResponse, ChatRequest } from '@/types/api.generated'

export function useChatHistory(chatId?: string) {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['chat', 'history', chatId],
    queryFn: async () => {
      if (!chatId) return []
      
      // For now, return empty array since chat history is managed by the store
      // This can be extended later when backend supports chat history persistence
      return [] as ChatMessage[]
    },
    enabled: !!chatId,
    staleTime: 5 * 60 * 1000, // 5 Minuten
    gcTime: 10 * 60 * 1000, // 10 Minuten
  })
}

export function useSendMessage() {
  const apiClient = useApiClient()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (request: ChatRequest): Promise<ChatResponse> => {
      const response = await apiClient.request<ChatResponse>({
        method: 'POST',
        url: '/query',
        data: {
          message: request.message,
          // Additional context if needed
          context: request.context
        }
      })
      return response
    },
    onSuccess: (data, variables) => {
      // Invalidate related queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['chat', 'history'] })
      
      // Optional: Update cache optimistically if we had server-side chat history
      // queryClient.setQueryData(
      //   ['chat', 'history', variables.chatId],
      //   (oldData: ChatMessage[]) => [...(oldData || []), newMessage]
      // )
    },
    onError: (error, variables) => {
      console.error('Failed to send message:', error)
      // Error handling is done by the calling component
    }
  })
}

export function useCreateChat() {
  const apiClient = useApiClient()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (initialMessage: string) => {
      // For now, we don't have a dedicated create chat endpoint
      // This would be used if the backend supports server-side chat management
      const response = await apiClient.request<{ chatId: string }>({
        method: 'POST',
        url: '/chat/create',
        data: { message: initialMessage }
      })
      return response
    },
    onSuccess: (data) => {
      // Invalidate chat lists to show new chat
      queryClient.invalidateQueries({ queryKey: ['chat', 'list'] })
      
      // Prefetch the new chat history
      queryClient.prefetchQuery({
        queryKey: ['chat', 'history', data.chatId],
        queryFn: () => [] as ChatMessage[], // Empty for now
      })
    },
    onError: (error) => {
      console.error('Failed to create chat:', error)
    }
  })
}

export function useChatList() {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['chat', 'list'],
    queryFn: async () => {
      // For now, return empty array since chat list is managed by the store
      // This can be extended later when backend supports chat list persistence
      return [] as Array<{ id: string; title: string; lastMessage: string }>
    },
    staleTime: 2 * 60 * 1000, // 2 Minuten
  })
} 