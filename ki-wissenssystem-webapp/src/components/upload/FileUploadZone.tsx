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
} from '@mui/material'
import {
  CloudUpload as CloudUploadIcon,
  Description as DocumentIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Folder as FolderIcon,
} from '@mui/icons-material'
import { getAPIClient } from '@/lib/api'

interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
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

  const addFiles = useCallback((newFiles: File[]) => {
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
  }, [acceptedTypes])

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

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files))
    }
  }

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }

  const uploadFile = async (uploadFile: UploadFile) => {
    setFiles(prev => prev.map(f => 
      f.id === uploadFile.id 
        ? { ...f, status: 'uploading', progress: 0 }
        : f
    ))

    try {
      const apiClient = getAPIClient()
      const formData = new FormData()
      formData.append('file', uploadFile.file)

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id && f.progress < 90
            ? { ...f, progress: f.progress + 10 }
            : f
        ))
      }, 200)

      const response = await apiClient.uploadDocument(formData)
      
      clearInterval(progressInterval)
      
      if (response) {
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'success', progress: 100 }
            : f
        ))
      }
    } catch (error) {
      console.error('Upload-Fehler:', error)
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

  const uploadAllFiles = async () => {
    setIsUploading(true)
    const pendingFiles = files.filter(f => f.status === 'pending')
    
    try {
      await Promise.all(pendingFiles.map(uploadFile))
    } finally {
      setIsUploading(false)
    }
  }

  const clearAllFiles = () => {
    setFiles([])
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'pdf':
        return <DocumentIcon color="error" />
      case 'doc':
      case 'docx':
        return <DocumentIcon color="primary" />
      case 'txt':
      case 'md':
        return <DocumentIcon color="action" />
      case 'xlsx':
      case 'xls':
      case 'csv':
        return <DocumentIcon color="success" />
      case 'pptx':
      case 'ppt':
        return <DocumentIcon color="warning" />
      default:
        return <DocumentIcon />
    }
  }

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />
      case 'error':
        return <ErrorIcon color="error" />
      default:
        return null
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const pendingCount = files.filter(f => f.status === 'pending').length
  const successCount = files.filter(f => f.status === 'success').length
  const errorCount = files.filter(f => f.status === 'error').length

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dokument-Upload
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Laden Sie Dokumente hoch, um sie in Ihr Wissenssystem zu integrieren
        </Typography>
      </Box>

      {/* Upload Zone */}
      <Paper
        elevation={isDragOver ? 4 : 1}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          p: 4,
          mb: 3,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragOver ? 'primary.main' : 'divider',
          bgcolor: isDragOver ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover'
          }
        }}
        onClick={handleFileSelect}
      >
        <CloudUploadIcon 
          sx={{ 
            fontSize: 64, 
            color: isDragOver ? 'primary.main' : 'text.secondary',
            mb: 2 
          }} 
        />
        <Typography variant="h6" gutterBottom>
          {isDragOver ? 'Dateien hier ablegen' : 'Dateien hochladen'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Ziehen Sie Dateien hierher oder klicken Sie zum Auswählen
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Unterstützte Formate: {acceptedTypes.join(', ')}
        </Typography>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </Paper>

      {/* File Statistics */}
      {files.length > 0 && (
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Chip 
            icon={<FolderIcon />}
            label={`${files.length} Dateien`} 
            variant="outlined" 
          />
          {pendingCount > 0 && (
            <Chip 
              label={`${pendingCount} ausstehend`} 
              color="default" 
              variant="outlined" 
            />
          )}
          {successCount > 0 && (
            <Chip 
              label={`${successCount} erfolgreich`} 
              color="success" 
              variant="outlined" 
            />
          )}
          {errorCount > 0 && (
            <Chip 
              label={`${errorCount} Fehler`} 
              color="error" 
              variant="outlined" 
            />
          )}
        </Box>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">
                Ausgewählte Dateien
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={uploadAllFiles}
                  disabled={pendingCount === 0 || isUploading}
                  startIcon={<CloudUploadIcon />}
                >
                  {isUploading ? 'Uploading...' : `${pendingCount} Dateien hochladen`}
                </Button>
                <Button
                  variant="outlined"
                  onClick={clearAllFiles}
                  disabled={isUploading}
                  startIcon={<DeleteIcon />}
                >
                  Alle löschen
                </Button>
              </Box>
            </Box>
          </Box>
          
          <List>
            {files.map((uploadFile, index) => (
              <ListItem key={uploadFile.id} divider={index < files.length - 1}>
                <ListItemIcon>
                  {getFileIcon(uploadFile.file.name)}
                </ListItemIcon>
                <ListItemText
                  primary={uploadFile.file.name}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatFileSize(uploadFile.file.size)}
                      </Typography>
                      {uploadFile.status === 'uploading' && (
                        <Box sx={{ mt: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={uploadFile.progress} 
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {uploadFile.progress}%
                          </Typography>
                        </Box>
                      )}
                      {uploadFile.error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {uploadFile.error}
                        </Alert>
                      )}
                    </Box>
                  }
                />
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getStatusIcon(uploadFile.status)}
                  <IconButton
                    onClick={() => removeFile(uploadFile.id)}
                    disabled={uploadFile.status === 'uploading'}
                    size="small"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {files.length === 0 && (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Keine Dateien ausgewählt
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Wählen Sie Dateien aus, um sie in Ihr Wissenssystem hochzuladen
          </Typography>
        </Paper>
      )}
    </Container>
  )
} 