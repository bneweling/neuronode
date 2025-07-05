'use client'

import { CloudUpload as CloudUploadIcon, Delete as DeleteIcon, Folder as FolderIcon } from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

import { useUploadDocument } from '@/hooks/useDocumentApi'

interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

export default function FileUploadZone() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const uploadMutation = useUploadDocument()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newUploads: UploadFile[] = acceptedFiles.map(file => ({
      id: `${file.name}-${file.lastModified}`,
      file,
      status: 'pending',
      progress: 0,
    }))
    setFiles(prev => [...prev, ...newUploads])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  const handleUpload = async (upload: UploadFile) => {
    setFiles(prev => prev.map(f => f.id === upload.id ? { ...f, status: 'uploading' } : f))
    
    try {
      await uploadMutation.mutateAsync({ file: upload.file })
      setFiles(prev => prev.map(f => f.id === upload.id ? { ...f, status: 'success', progress: 100 } : f))
    } catch (e) {
      const error = e as Error
      setFiles(prev => prev.map(f => f.id === upload.id ? { ...f, status: 'error', error: error.message } : f))
    }
  }

  const handleUploadAll = () => {
    files.filter(f => f.status === 'pending').forEach(handleUpload)
  }
  
  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          border: `2px dashed ${isDragActive ? 'primary.main' : 'grey.400'}`,
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          mb: 3
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 60, color: 'text.secondary' }} />
        <Typography variant="h6">Dateien per Drag & Drop hier ablegen oder klicken zum Auswählen</Typography>
        <Typography variant="body2" color="text.secondary">PDF, DOCX, TXT, etc.</Typography>
      </Paper>
      
      {uploadMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Ein Fehler ist aufgetreten: {uploadMutation.error.message}
        </Alert>
      )}

      <List>
        {files.map(upload => (
          <ListItem
            key={upload.id}
            secondaryAction={
              <>
                {upload.status === 'pending' && <Button onClick={() => handleUpload(upload)}>Upload</Button>}
                <IconButton edge="end" onClick={() => removeFile(upload.id)}>
                  <DeleteIcon />
                </IconButton>
              </>
            }
          >
            <ListItemText primary={upload.file.name} secondary={upload.status} />
            {(upload.status === 'uploading' || uploadMutation.isPending && files.some(f => f.id === upload.id)) && <LinearProgress variant="indeterminate" sx={{width: '50%'}}/>}
            {upload.status === 'success' && <Typography color="green">Erfolgreich!</Typography>}
            {upload.status === 'error' && <Typography color="red">{upload.error}</Typography>}
          </ListItem>
        ))}
      </List>
      
      <Button
        variant="contained"
        onClick={handleUploadAll}
        disabled={files.every(f => f.status !== 'pending') || uploadMutation.isPending}
        sx={{ mt: 2 }}
      >
        {uploadMutation.isPending ? <CircularProgress size={24} /> : 'Alle hochladen'}
      </Button>
    </Box>
  )
}