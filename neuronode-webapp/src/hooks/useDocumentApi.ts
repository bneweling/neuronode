import { useMutation, useQueryClient } from '@tanstack/react-query'

import { useApiClient } from '@/contexts/ApiClientContext'
import { components } from '@/types/api.generated'

type DocumentUploadResponse = components['schemas']['DocumentUploadResponse']

interface UploadRequest {
  file: File
}

export const useUploadDocument = () => {
  const apiClient = useApiClient()
  const queryClient = useQueryClient()

  return useMutation<DocumentUploadResponse, Error, UploadRequest>({
    mutationFn: async ({ file }) => {
      // The apiClient's uploadDocument method handles FormData and headers
      return apiClient.uploadDocument(file)
    },
    onSuccess: (data) => {
      // Invalidate queries that should be updated after a successful upload
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['graphData'] })
      queryClient.invalidateQueries({ queryKey: ['graphStats'] })
      console.log('Upload successful, invalidated relevant queries.', data)
    },
    onError: (error) => {
      console.error('Document upload failed:', error)
    },
  })
} 