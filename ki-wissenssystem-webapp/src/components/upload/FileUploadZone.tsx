'use client'

import { useState, useRef, useCallback } from 'react'
import { useAPI, DocumentUploadResponse } from '@/lib/api'
import { useMaterialTheme } from '@/lib/theme'

interface UploadedFile {
  file: File
  status: 'uploading' | 'success' | 'error'
  progress: number
  response?: DocumentUploadResponse
  error?: string
  preview?: string
}

export default function FileUploadZone() {
  const api = useAPI()
  const { breakpoint } = useMaterialTheme()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null)

  // Handle drag events
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    processFiles(droppedFiles)
  }, [])

  // File processing
  const processFiles = async (fileList: File[]) => {
    const validFiles = fileList.filter(file => {
      // Basic file validation
      const maxSize = 50 * 1024 * 1024 // 50MB
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ]

      if (file.size > maxSize) {
        console.warn(`File ${file.name} is too large (${(file.size / 1024 / 1024).toFixed(1)}MB)`)
        return false
      }

      if (!allowedTypes.includes(file.type) && !file.name.match(/\.(txt|md|pdf|docx?|xlsx?)$/i)) {
        console.warn(`File ${file.name} has unsupported type: ${file.type}`)
        return false
      }

      return true
    })

    // Create upload entries
    const uploadFiles: UploadedFile[] = validFiles.map(file => ({
      file,
      status: 'uploading' as const,
      progress: 0
    }))

    setFiles(prev => [...prev, ...uploadFiles])

    // Process each file
    for (let i = 0; i < uploadFiles.length; i++) {
      const uploadFile = uploadFiles[i]
      await processSingleFile(uploadFile, files.length + i)
    }
  }

  const processSingleFile = async (uploadFile: UploadedFile, index: number) => {
    try {
      // Simulate progress for demo
      const updateProgress = (progress: number) => {
        setFiles(prev => 
          prev.map((f, i) => 
            i === index ? { ...f, progress } : f
          )
        )
      }

      // First, analyze the file
      updateProgress(10)
      const preview = await api.analyzeDocumentPreview(uploadFile.file)
      
      updateProgress(30)
      
      // Generate text preview
      const textPreview = `${preview.predicted_document_type}\n\n${preview.preview_text.substring(0, 500)}...`
      
      updateProgress(50)
      
      // Upload the document
      const response = await api.uploadDocument(uploadFile.file)
      
      updateProgress(100)

      setFiles(prev => 
        prev.map((f, i) => 
          i === index ? { 
            ...f, 
            status: 'success' as const, 
            response,
            preview: textPreview
          } : f
        )
      )

    } catch (error) {
      console.error('Upload failed:', error)
      setFiles(prev => 
        prev.map((f, i) => 
          i === index ? { 
            ...f, 
            status: 'error' as const, 
            error: String(error)
          } : f
        )
      )
    }
  }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      processFiles(Array.from(e.target.files))
    }
  }

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf': 
        return <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z"/>
        </svg>
      case 'doc':
      case 'docx': 
        return <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
      case 'xls':
      case 'xlsx': 
        return <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
      case 'txt': 
        return <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
      case 'md': 
        return <svg className="w-5 h-5 text-purple-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
      default: 
        return <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const clearFiles = () => {
    setFiles([])
    setSelectedFile(null)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Upload Header */}
      <div className="app-header md-elevation-1 p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
              </svg>
            </div>
            <div>
              <h2 className="md-headline-large text-lg font-semibold">
                Dokument Upload
              </h2>
              <div className="text-sm opacity-60">
                Erweitern Sie Ihr Wissenssystem
              </div>
            </div>
          </div>
          
          {files.length > 0 && (
            <button
              onClick={clearFiles}
              className="md-surface hover:md-elevation-2 md-shape-medium px-4 py-2 text-sm md-motion-short flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
              <span>Alle löschen</span>
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Upload Zone */}
        <div className="flex-1 p-6">
          <div
            className={`upload-zone h-64 cursor-pointer md-motion-short ${
              dragActive ? 'drag-over' : ''
            }`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={handleFileSelect}
          >
            <div className="flex flex-col items-center justify-center h-full space-y-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </div>
              <div className="text-center">
                <h3 className="md-headline-large text-lg font-semibold mb-2">
                  Dateien hierher ziehen
                </h3>
                <p className="md-body-large text-gray-600 mb-4">
                  oder klicken Sie, um Dateien auszuwählen
                </p>
                <div className="text-sm opacity-60 space-y-2 bg-surface-variant rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                    </svg>
                    <span>Unterstützte Formate: PDF, Word, Excel, TXT, Markdown</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A0.5,0.5 0 0,0 7,13.5A0.5,0.5 0 0,0 7.5,14A0.5,0.5 0 0,0 8,13.5A0.5,0.5 0 0,0 7.5,13M16.5,13A0.5,0.5 0 0,0 16,13.5A0.5,0.5 0 0,0 16.5,14A0.5,0.5 0 0,0 17,13.5A0.5,0.5 0 0,0 16.5,13Z"/>
                    </svg>
                    <span>Maximale Größe: 50MB pro Datei</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.md,.xls,.xlsx"
            onChange={handleFileInput}
            className="hidden"
          />

          {/* Upload Progress */}
          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              <h3 className="md-headline-large text-lg font-semibold">
                Upload Status ({files.length} Dateien)
              </h3>
              
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {files.map((uploadFile, index) => (
                  <div
                    key={index}
                    className="md-surface md-elevation-1 md-shape-medium p-4 cursor-pointer hover:md-elevation-2 md-motion-short"
                    onClick={() => setSelectedFile(uploadFile)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">{getFileIcon(uploadFile.file.name)}</div>
                      
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium">{uploadFile.file.name}</span>
                          <span className="text-sm opacity-60">
                            {formatFileSize(uploadFile.file.size)}
                          </span>
                        </div>
                        
                        {uploadFile.status === 'uploading' && (
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full md-motion-medium"
                              style={{ width: `${uploadFile.progress}%` }}
                            ></div>
                          </div>
                        )}
                        
                        {uploadFile.status === 'success' && (
                          <div className="text-sm text-green-600 flex items-center space-x-2">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                            </svg>
                            <span>Erfolgreich verarbeitet</span>
                            {uploadFile.response && (
                              <span className="opacity-60">
                                ({uploadFile.response.num_chunks} Chunks)
                              </span>
                            )}
                          </div>
                        )}
                        
                        {uploadFile.status === 'error' && (
                          <div className="text-sm text-red-600 flex items-center space-x-2">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"/>
                            </svg>
                            <span>Fehler beim Upload</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* File Details Sidebar */}
        {selectedFile && (
          <div className="w-80 app-sidebar p-4 overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="md-headline-medium font-semibold">
                  Dateidetails
                </h3>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="p-1 hover:bg-gray-200 rounded"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                  </svg>
                </button>
              </div>

              <div className="md-surface md-elevation-1 md-shape-medium p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="flex-shrink-0">{getFileIcon(selectedFile.file.name)}</div>
                  <div>
                    <h4 className="font-semibold">{selectedFile.file.name}</h4>
                    <div className="text-sm opacity-60">
                      {formatFileSize(selectedFile.file.size)}
                    </div>
                  </div>
                </div>

                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium">Status:</span>
                    <div className="mt-1">
                      {selectedFile.status === 'uploading' && (
                        <span className="text-blue-600 flex items-center space-x-2">
                          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                          <span>Wird verarbeitet... {selectedFile.progress}%</span>
                        </span>
                      )}
                      {selectedFile.status === 'success' && (
                        <span className="text-green-600 flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                          </svg>
                          <span>Erfolgreich verarbeitet</span>
                        </span>
                      )}
                      {selectedFile.status === 'error' && (
                        <span className="text-red-600 flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"/>
                          </svg>
                          <span>Fehler: {selectedFile.error}</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {selectedFile.response && (
                    <div>
                      <span className="font-medium">Verarbeitung:</span>
                      <div className="mt-1 space-y-1">
                        <div>Dokumenttyp: {selectedFile.response.document_type || 'Unbekannt'}</div>
                        <div>Chunks: {selectedFile.response.num_chunks || 0}</div>
                        <div>Controls: {selectedFile.response.num_controls || 0}</div>
                      </div>
                    </div>
                  )}

                  {selectedFile.preview && (
                    <div>
                      <span className="font-medium">Vorschau:</span>
                      <div className="mt-1 p-3 md-surface-variant md-shape-small text-xs max-h-40 overflow-y-auto">
                        <pre className="whitespace-pre-wrap font-mono">
                          {selectedFile.preview}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {selectedFile.status === 'success' && (
                <button
                  onClick={() => {
                    // Could navigate to chat or graph to explore the uploaded content
                    console.log('Explore uploaded document:', selectedFile.response)
                  }}
                  className="w-full md-primary md-shape-medium py-2 hover:md-elevation-1 md-motion-short"
                >
                  🔍 Inhalt erkunden
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 