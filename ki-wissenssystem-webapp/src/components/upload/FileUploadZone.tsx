'use client'

import { useState, useRef, useCallback, useMemo } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Alert,
  Chip,
  Container,
  IconButton,
  Card,
  CardContent,
  Divider,
} from '@mui/material'
import {
  CloudUpload as CloudUploadIcon,
  Description as DocumentIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Folder as FolderIcon,
  Analytics as AnalyticsIcon,
  AccountTree as GraphIcon,
} from '@mui/icons-material'
import { getAPIClient } from '@/lib/serviceFactory'

interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'analyzing' | 'uploading' | 'processing' | 'success' | 'error'
  progress: number
  error?: string
  analysis?: DocumentAnalysis
  result?: ProcessingResult
  taskId?: string
  currentStep?: string
}

interface DocumentAnalysis {
  predicted_document_type: string
  file_type: string
  preview_text: string
  processing_estimate: {
    estimated_duration_seconds: number
    estimated_chunks: number
    will_extract_controls: boolean
    processing_steps: string[]
  }
  confidence_indicators: {
    type_detection: string
    classification: string
  }
  estimated_processing_time?: string
  estimated_chunk_count?: number
  estimated_control_count?: number
  preview_image?: string
  file_size_mb?: number
  complexity_score?: number
  warnings?: string[]
}

interface DocumentAnalysisResponse extends DocumentAnalysis {
  status?: string
  message?: string
  [key: string]: any
}

interface UploadResponse {
  success: boolean
  id?: string
  status?: string
  task_id?: string
  filename?: string
  document_type?: string
  num_chunks?: number
  num_controls?: number
  metadata?: any
  processing_duration?: number
  quality_score?: number
  extracted_entities?: string[]
  graph_nodes_created?: number
  graph_relationships_created?: number
}

interface ProcessingResult {
  filename: string
  status: string
  document_type?: string
  num_chunks?: number
  num_controls?: number
  metadata?: any
  processing_duration?: number
  quality_score?: number
  extracted_entities?: string[]
  graph_nodes_created?: number
  graph_relationships_created?: number
}

interface ProcessingStatus {
  task_id: string
  status: string
  progress: number
  steps_completed: string[]
  current_step: string
  estimated_completion: string
  current_operation?: string
  llm_metadata?: {
    model_used?: string
    tokens_processed?: number
    confidence?: number
  }
  processing_start_time?: string
  processing_end_time?: string
}

export default function FileUploadZone() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const acceptedTypes = useMemo(() => [
    '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf',
    '.xlsx', '.xls', '.csv', '.pptx', '.ppt'
  ], [])

  const addFiles = useCallback(async (newFiles: File[]) => {
    const validFiles = newFiles.filter(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase()
      return acceptedTypes.includes(extension)
    })

    const uploadFiles: UploadFile[] = validFiles.map(file => ({
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending',
      progress: 0
    }))

    setFiles(prev => [...prev, ...uploadFiles])

    // Sofortige Analyse für jede Datei
    for (const uploadFile of uploadFiles) {
      await analyzeFile(uploadFile)
    }
  }, [acceptedTypes])

  const analyzeFile = async (uploadFile: UploadFile) => {
    setFiles(prev => prev.map(f => 
      f.id === uploadFile.id 
        ? { ...f, status: 'analyzing', progress: 10 }
        : f
    ))

    try {
      const apiClient = getAPIClient()
      const formData = new FormData()
      formData.append('file', uploadFile.file)

      const analysis = await apiClient.analyzeDocumentPreview(formData) as DocumentAnalysisResponse
      
      // Erfolgreiche Analyse - verwende die Daten direkt
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'pending',
              progress: 0,
              analysis: {
                predicted_document_type: analysis.predicted_document_type || 'unknown',
                file_type: analysis.file_type || 'unknown', 
                preview_text: analysis.preview_text || 'Vorschau nicht verfügbar',
                processing_estimate: analysis.processing_estimate || {
                  estimated_duration_seconds: 30,
                  estimated_chunks: 1,
                  will_extract_controls: false,
                  processing_steps: ['Basic processing']
                },
                confidence_indicators: analysis.confidence_indicators || {
                  type_detection: 'medium',
                  classification: 'success'
                },
                estimated_processing_time: analysis.estimated_processing_time,
                estimated_chunk_count: analysis.estimated_chunk_count,
                estimated_control_count: analysis.estimated_control_count,
                preview_image: analysis.preview_image,
                file_size_mb: analysis.file_size_mb,
                complexity_score: analysis.complexity_score,
                warnings: analysis.warnings
              },
              error: (analysis.warnings && analysis.warnings.length > 0) ? `Warnung: ${analysis.warnings[0]}` : undefined
            }
          : f
      ))
      
    } catch (error) {
      console.error('Analyse-Fehler:', error)
      
      // Enhanced error handling with user-friendly messages
      let errorMessage = 'Analyse fehlgeschlagen'
      let allowUpload = true
      
      if (error instanceof Error) {
        if (error.message?.includes('quota') || error.message?.includes('429')) {
          errorMessage = 'API-Limit erreicht - Upload trotzdem möglich'
          allowUpload = true
        } else if (error.message?.includes('network') || error.message?.includes('fetch')) {
          errorMessage = 'Netzwerkfehler - Upload trotzdem möglich'
          allowUpload = true
        }
      }
      
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: allowUpload ? 'pending' : 'error',
              progress: 0,
              error: errorMessage,
              analysis: allowUpload ? {
                predicted_document_type: 'unknown',
                file_type: uploadFile.file.name.split('.').pop()?.toLowerCase() || 'unknown',
                preview_text: 'Vorschau aufgrund von API-Problemen nicht verfügbar',
                processing_estimate: {
                  estimated_duration_seconds: 60,
                  estimated_chunks: Math.max(1, Math.floor(uploadFile.file.size / 10000)),
                  will_extract_controls: false,
                  processing_steps: ['File upload', 'Basic processing', 'Content extraction']
                },
                confidence_indicators: {
                  type_detection: 'medium',
                  classification: 'fallback'
                },
                estimated_processing_time: 'Nicht verfügbar',
                estimated_chunk_count: 0,
                estimated_control_count: 0,
                preview_image: 'Nicht verfügbar',
                file_size_mb: 0,
                complexity_score: 0,
                warnings: ['API-Fehler']
              } : undefined
            }
          : f
      ))
    }
  }

  const uploadSingleFile = async (uploadFile: UploadFile) => {
    setFiles(prev => prev.map(f => 
      f.id === uploadFile.id 
        ? { ...f, status: 'uploading', progress: 0 }
        : f
    ))

    try {
      const apiClient = getAPIClient()
      const formData = new FormData()
      formData.append('file', uploadFile.file)

      // Upload-Progress simulieren bis 30%
      const uploadInterval = setInterval(() => {
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id && f.progress < 30
            ? { ...f, progress: Math.min(f.progress + 5, 30) }
            : f
        ))
      }, 100)

      try {
        const response = await apiClient.uploadDocument(formData) as UploadResponse
        
        clearInterval(uploadInterval)
        
        if (response && response.success) {
          if (response.status === 'processing' && response.task_id) {
            // Background processing - Status überwachen
            setFiles(prev => prev.map(f => 
              f.id === uploadFile.id 
                ? { 
                    ...f, 
                    status: 'processing',
                    progress: 40,
                    taskId: response.task_id
                  }
                : f
            ))
            
            await monitorProcessing(uploadFile.id, response.task_id)
          } else if (response.status === 'completed') {
            // Sofort abgeschlossen - direkte Verarbeitung erfolgreich
            setFiles(prev => prev.map(f => 
              f.id === uploadFile.id 
                ? { 
                    ...f, 
                    status: 'success' as const,
                    progress: 100,
                    result: {
                      filename: response.filename || uploadFile.file.name,
                      status: response.status || 'completed',
                      document_type: response.document_type || 'unknown',
                      num_chunks: response.num_chunks || 0,
                      num_controls: response.num_controls || 0,
                      metadata: response.metadata || {},
                      processing_duration: response.processing_duration,
                      quality_score: response.quality_score,
                      extracted_entities: response.extracted_entities,
                      graph_nodes_created: response.graph_nodes_created,
                      graph_relationships_created: response.graph_relationships_created
                    }
                  }
                : f
            ))
          } else if (response.status === 'upload_only' || response.status === 'processed_simple') {
            // Teilweise erfolgreich - Upload OK, aber Processing eingeschränkt
            setFiles(prev => prev.map(f => 
              f.id === uploadFile.id 
                ? { 
                    ...f, 
                    status: 'success' as const,
                    progress: 100,
                    result: {
                      filename: response.filename || uploadFile.file.name,
                      status: response.status || 'processed',
                      document_type: response.document_type || 'unknown',
                      num_chunks: response.num_chunks || 0,
                      num_controls: response.num_controls || 0,
                      metadata: response.metadata || {},
                      processing_duration: response.processing_duration,
                      quality_score: response.quality_score,
                      extracted_entities: response.extracted_entities,
                      graph_nodes_created: response.graph_nodes_created,
                      graph_relationships_created: response.graph_relationships_created
                    }
                  }
                : f
            ))
          }
        } else {
          throw new Error('Upload response indicates failure')
        }
      } catch (uploadError) {
        clearInterval(uploadInterval)
        throw uploadError
      }
    } catch (error) {
      console.error('Upload-Fehler:', error)
      const errorMessage = error instanceof Error ? error.message : 'Upload fehlgeschlagen'
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'error', 
              progress: 0,
              error: 'Upload fehlgeschlagen. Bitte versuchen Sie es erneut.'
            }
          : f
      ))
    }
  }

  const monitorProcessing = async (fileId: string, taskId: string) => {
    const maxAttempts = 60 // 5 Minuten
    let attempts = 0

    const checkStatus = async () => {
      try {
        const apiClient = getAPIClient()
        const status: ProcessingStatus = await apiClient.getProcessingStatus(taskId)
        
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { 
                ...f, 
                progress: Math.min(40 + (status.progress * 60), 100),
                currentStep: status.current_step,
                current_operation: status.current_operation,
                llm_metadata: status.llm_metadata,
                processing_start_time: status.processing_start_time,
                processing_end_time: status.processing_end_time
              }
            : f
        ))

        if (status.status === 'completed') {
          setFiles(prev => prev.map(f => 
            f.id === fileId 
              ? { 
                  ...f, 
                  status: 'success',
                  progress: 100,
                  result: {
                    filename: f.file.name,
                    status: 'completed',
                    document_type: 'unknown',
                    num_chunks: 0,
                    num_controls: 0,
                    metadata: {},
                    processing_duration: 0,
                    quality_score: 1.0,
                    extracted_entities: [],
                    graph_nodes_created: 0,
                    graph_relationships_created: 0
                  }
                }
              : f
          ))
          return
        } else if (status.status === 'failed' || status.status === 'error') {
          throw new Error('Verarbeitung fehlgeschlagen')
        }

        attempts++
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 5000)
        } else {
          throw new Error('Timeout bei der Verarbeitung')
        }

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unbekannter Fehler'
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { 
                ...f, 
                status: 'error',
                error: `Verarbeitung fehlgeschlagen: ${errorMessage}`
              }
            : f
        ))
      }
    }

    checkStatus()
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }, [addFiles])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files ? Array.from(e.target.files) : []
    addFiles(selectedFiles)
  }, [addFiles])

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }

  const uploadAllFiles = async () => {
    setIsUploading(true)
    const pendingFiles = files.filter(f => f.status === 'pending')
    
    for (const file of pendingFiles) {
      await uploadSingleFile(file)
    }
    
    setIsUploading(false)
  }

  const getFileIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'pdf':
        return <DocumentIcon sx={{ color: '#d32f2f' }} />
      case 'doc':
      case 'docx':
        return <DocumentIcon sx={{ color: '#1976d2' }} />
      case 'xls':
      case 'xlsx':
        return <DocumentIcon sx={{ color: '#388e3c' }} />
      case 'ppt':
      case 'pptx':
        return <DocumentIcon sx={{ color: '#f57c00' }} />
      default:
        return <DocumentIcon />
    }
  }

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'analyzing':
        return <AnalyticsIcon sx={{ color: '#2196f3' }} />
      case 'uploading':
        return <CloudUploadIcon sx={{ color: '#ff9800' }} />
      case 'processing':
        return <CloudUploadIcon sx={{ color: '#ff9800' }} />
      case 'success':
        return <CheckCircleIcon sx={{ color: '#4caf50' }} />
      case 'error':
        return <ErrorIcon sx={{ color: '#f44336' }} />
      default:
        return <DocumentIcon />
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        📄 Dokumente hochladen
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 4 }}>
        Laden Sie Ihre Dokumente hoch für automatische Analyse und Knowledge Graph Integration.
      </Typography>

      {/* Upload Zone */}
      <Paper
        elevation={2}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          border: '2px dashed',
          borderColor: isDragOver ? 'primary.main' : 'grey.300',
          backgroundColor: isDragOver ? 'action.hover' : 'background.paper',
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          mb: 3
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Dateien hier ablegen oder klicken zum Auswählen
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Unterstützte Formate: PDF, Word, Excel, PowerPoint, Text
        </Typography>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          multiple
          accept={acceptedTypes.join(',')}
          style={{ display: 'none' }}
        />
      </Paper>

      {/* File List */}
      {files.length > 0 && (
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" component="h2" gutterBottom>
              📋 Upload-Liste ({files.length} {files.length === 1 ? 'Datei' : 'Dateien'})
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<CloudUploadIcon />}
                onClick={uploadAllFiles}
                disabled={isUploading || files.filter(f => f.status === 'pending').length === 0}
              >
                Alle hochladen ({files.filter(f => f.status === 'pending').length})
              </Button>
              <Button
                variant="outlined"
                onClick={() => setFiles([])}
                disabled={isUploading}
              >
                Liste leeren
              </Button>
            </Box>
          </Box>

          <List>
            {files.map((uploadFile) => (
              <FileCard 
                key={uploadFile.id} 
                uploadFile={uploadFile} 
                onRemove={removeFile}
                onUpload={() => uploadSingleFile(uploadFile)}
                isUploading={isUploading}
              />
            ))}
          </List>
        </Paper>
      )}

      {/* Help Text */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>💡 Tipp:</strong> Das System erkennt automatisch Dokumenttypen wie BSI IT-Grundschutz, 
          ISO 27001, NIST CSF und andere Compliance-Standards. Nach dem Upload können Sie die 
          Ergebnisse direkt im Knowledge Graph visualisieren oder per Chat abfragen.
        </Typography>
      </Alert>
    </Container>
  )
}

interface FileCardProps {
  uploadFile: UploadFile
  onRemove: (id: string) => void
  onUpload: () => void
  isUploading: boolean
}

const FileCard = ({ uploadFile, onRemove, onUpload, isUploading }: FileCardProps) => {
  const getStatusText = () => {
    switch (uploadFile.status) {
      case 'analyzing': return 'Analysiere Dokument...'
      case 'uploading': return 'Lade hoch...'
      case 'processing': return uploadFile.currentStep ? `Verarbeite: ${uploadFile.currentStep}` : 'Verarbeite Dokument...'
      case 'success': return 'Erfolgreich verarbeitet'
      case 'error': return uploadFile.error || 'Fehler aufgetreten'
      default: return 'Bereit zum Upload'
    }
  }

  const getStatusColor = () => {
    switch (uploadFile.status) {
      case 'analyzing': return '#2196f3'
      case 'uploading': return '#ff9800'
      case 'processing': return '#ff9800'
      case 'success': return '#4caf50'
      case 'error': return '#f44336'
      default: return '#666'
    }
  }

  return (
    <Card sx={{ mb: 2, border: `1px solid ${getStatusColor()}` }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <DocumentIcon />
            <Box>
              <Typography variant="h6" component="div">
                {uploadFile.file.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {(uploadFile.file.size / 1024 / 1024).toFixed(2)} MB
              </Typography>
              {uploadFile.analysis && (
                <Chip 
                  label={uploadFile.analysis.predicted_document_type}
                  size="small"
                  color="primary"
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            {uploadFile.status === 'pending' && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<CloudUploadIcon />}
                onClick={onUpload}
                disabled={isUploading}
              >
                Upload starten
              </Button>
            )}
            <IconButton
              size="small"
              onClick={() => onRemove(uploadFile.id)}
              disabled={isUploading}
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Progress Bar */}
        {(uploadFile.status === 'analyzing' || uploadFile.status === 'uploading' || uploadFile.status === 'processing') && (
          <Box mt={2}>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
              <Typography variant="body2">{getStatusText()}</Typography>
              <Typography variant="body2">{uploadFile.progress}%</Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={uploadFile.progress} 
              sx={{
                height: 6,
                borderRadius: 3,
                '& .MuiLinearProgress-bar': {
                  backgroundColor: getStatusColor()
                }
              }}
            />
          </Box>
        )}

        {/* Success Results */}
        {uploadFile.result && uploadFile.status === 'success' && (
          <Box mt={2}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              🎉 Verarbeitungsergebnisse:
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
              {uploadFile.result.document_type && (
                <Chip label={`Typ: ${uploadFile.result.document_type}`} size="small" />
              )}
              {uploadFile.result.num_chunks && (
                <Chip label={`${uploadFile.result.num_chunks} Chunks`} size="small" />
              )}
              {uploadFile.result.num_controls && (
                <Chip label={`${uploadFile.result.num_controls} Controls`} size="small" />
              )}
            </Box>
            <Box display="flex" gap={1} flexWrap="wrap">
              <Button
                variant="outlined"
                startIcon={<GraphIcon />}
                size="small"
                onClick={() => {
                  window.open('/graph', '_blank')
                }}
              >
                Im Graph ansehen
              </Button>
              <Button
                variant="outlined"
                startIcon={<DocumentIcon />}
                size="small"
                onClick={() => {
                  window.open(`/chat?doc=${uploadFile.result?.filename}`, '_blank')
                }}
              >
                Chat starten
              </Button>
            </Box>
          </Box>
        )}

        {/* Error Display */}
        {uploadFile.status === 'error' && uploadFile.error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {uploadFile.error}
          </Alert>
        )}
      </CardContent>
    </Card>
  )
} 