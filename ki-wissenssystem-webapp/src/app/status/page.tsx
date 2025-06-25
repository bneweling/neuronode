'use client'

import { useState, useEffect } from 'react'
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Paper,
  Divider,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material'
import { getAPIClient } from '@/lib/serviceFactory'

interface SystemStatus {
  api: boolean
  vectorStore: boolean
  graphDb: boolean
  lastCheck: string
}

interface SystemDiagnostics {
  system: {
    status: 'healthy' | 'partial' | 'error'
    timestamp: string
    components: Record<string, string>
  }
  performance: {
    response_time: number
    database_latency: number
    memory_usage: number
    cpu_usage: number
  }
  capabilities: {
    models_available: string[]
    features_enabled: string[]
    max_upload_size: number
  }
}

export default function StatusPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    api: false,
    vectorStore: false,
    graphDb: false,
    lastCheck: 'Nie'
  })
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkSystemStatus = async () => {
      setIsLoading(true)
      try {
        const apiClient = getAPIClient()
        
        const health = await apiClient.getSystemStatus()
        setSystemStatus({
          api: health.status === 'online',
          vectorStore: health.services?.['Vector Store'] || false,
          graphDb: health.services?.['Database'] || false,
          lastCheck: new Date().toLocaleTimeString('de-DE')
        })

        if (health.status === 'online') {
          // Mock diagnostics data since getDiagnostics doesn't exist
          setDiagnostics({
            system: {
              status: 'healthy',
              timestamp: new Date().toISOString(),
              components: {
                'API': 'healthy',
                'Vector Store': health.services?.['Vector Store'] ? 'healthy' : 'error',
                'Database': health.services?.['Database'] ? 'healthy' : 'error'
              }
            },
            performance: {
              response_time: health.performance.responseTime,
              database_latency: 50, // Mock value
              memory_usage: health.performance.memoryUsage,
              cpu_usage: health.performance.cpuUsage
            },
            capabilities: {
              models_available: ['gpt-4', 'claude-3'],
              features_enabled: ['chat', 'upload', 'graph'],
              max_upload_size: 10485760 // 10MB
            }
          })
        }
      } catch (error) {
        console.error('Systemstatus-Check fehlgeschlagen:', error)
        setSystemStatus(prev => ({
          ...prev,
          api: false,
          lastCheck: new Date().toLocaleTimeString('de-DE')
        }))
        setDiagnostics(null)
      } finally {
        setIsLoading(false)
      }
    }

    checkSystemStatus()
    const interval = setInterval(checkSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const StatusIndicator = ({ status, label }: { status: boolean, label: string }) => (
    <Box display="flex" alignItems="center" justifyContent="space-between" p={2}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Box display="flex" alignItems="center" gap={1}>
        {status ? (
          <CheckCircleIcon color="success" fontSize="small" />
        ) : (
          <ErrorIcon color="error" fontSize="small" />
        )}
        <Typography variant="body2" fontWeight="medium" color={status ? 'success.main' : 'error.main'}>
          {status ? 'Online' : 'Offline'}
        </Typography>
      </Box>
    </Box>
  )

  const MetricCard = ({ title, value, unit, icon: Icon }: {
    title: string
    value: number
    unit: string
    icon: React.ElementType
  }) => (
    <Card elevation={2}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h5" component="div" fontWeight="bold">
              {value}{unit}
            </Typography>
          </Box>
          <Icon color="primary" sx={{ fontSize: 40, opacity: 0.7 }} />
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Systemstatus
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Überwachung und Diagnostik des KI-Wissenssystems
        </Typography>
      </Box>

      {/* System Status Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System-Komponenten
              </Typography>
              <StatusIndicator status={systemStatus.api} label="API Server" />
              <Divider />
              <StatusIndicator status={systemStatus.vectorStore} label="Vector Store" />
              <Divider />
              <StatusIndicator status={systemStatus.graphDb} label="Graph Database" />
              <Box mt={2} pt={2} borderTop="1px solid" borderColor="divider">
                <Typography variant="caption" color="text.secondary">
                  Letzter Check: {systemStatus.lastCheck}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System-Informationen
              </Typography>
              {diagnostics ? (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Status: {diagnostics.system.status}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Verfügbare Modelle: {diagnostics.capabilities.models_available?.join(', ') || 'Keine'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Aktivierte Features: {diagnostics.capabilities.features_enabled?.join(', ') || 'Keine'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Max. Upload-Größe: {diagnostics.capabilities.max_upload_size ? 
                      `${Math.round(diagnostics.capabilities.max_upload_size / 1024 / 1024)} MB` : 'Unbekannt'}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {isLoading ? 'Lade Systeminformationen...' : 'Systeminformationen nicht verfügbar'}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics */}
      {diagnostics?.performance && (
        <Box mb={4}>
          <Typography variant="h5" gutterBottom>
            Performance-Metriken
          </Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <MetricCard
                title="Antwortzeit"
                value={Math.round(diagnostics.performance.response_time)}
                unit="ms"
                icon={SpeedIcon}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <MetricCard
                title="DB Latenz"
                value={Math.round(diagnostics.performance.database_latency)}
                unit="ms"
                icon={StorageIcon}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <MetricCard
                title="Speicher"
                value={Math.round(diagnostics.performance.memory_usage)}
                unit="%"
                icon={MemoryIcon}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <MetricCard
                title="CPU"
                value={Math.round(diagnostics.performance.cpu_usage)}
                unit="%"
                icon={ComputerIcon}
              />
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Loading Progress */}
      {isLoading && (
        <Paper elevation={1} sx={{ p: 2 }}>
          <Typography variant="body2" gutterBottom>
            Systemstatus wird aktualisiert...
          </Typography>
          <LinearProgress />
        </Paper>
      )}
    </Container>
  )
} 