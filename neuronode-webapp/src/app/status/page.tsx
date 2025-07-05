'use client'

import { useEffect } from 'react'
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Divider,
  useTheme
} from '@mui/material'
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as PerformanceIcon,
  Timeline as MetricsIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'

import { useSystemStatus, useSystemMetrics, useSystemHealth } from '@/hooks/useSystemStatus'
import { PerformanceMonitor } from '@/lib/performance'
import { TablerCard, TablerCardContent, TablerBox, TablerTypography, TablerContainer } from '@/components/ui'

export default function StatusPage() {
  const theme = useTheme()
  
  // Performance Monitoring
  useEffect(() => {
    PerformanceMonitor.trackPageLoad('StatusPage')
  }, [])

  // System Data Queries
  const { data: systemStatus, isLoading: statusLoading, error: statusError } = useSystemStatus()
  const { data: systemMetrics, isLoading: metricsLoading, error: metricsError } = useSystemMetrics()
  const { data: systemHealth, isLoading: healthLoading, error: healthError } = useSystemHealth()

  // Helper Functions
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'ok':
      case 'online':
        return 'success'
      case 'warning':
      case 'degraded':
        return 'warning'
      case 'error':
      case 'offline':
      case 'critical':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'ok':
      case 'online':
        return <HealthyIcon color="success" />
      case 'warning':
      case 'degraded':
        return <WarningIcon color="warning" />
      case 'error':
      case 'offline':
      case 'critical':
        return <ErrorIcon color="error" />
      default:
        return <RefreshIcon color="disabled" />
    }
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${days}d ${hours}h ${minutes}m`
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  // Loading State
  if (statusLoading || metricsLoading || healthLoading) {
    return (
      <>
        <header>
          <h1 style={{ display: 'none' }}>System Status</h1>
        </header>
        <main>
          <TablerContainer variant="page">
            <TablerBox variant="flex-center" style={{ minHeight: 400 }}>
              <CircularProgress size={60} />
            </TablerBox>
          </TablerContainer>
        </main>
      </>
    )
  }

  // Error State
  if (statusError || metricsError || healthError) {
    return (
      <>
        <header>
          <h1 style={{ display: 'none' }}>System Status</h1>
        </header>
        <main>
          <TablerContainer variant="page">
            <Alert severity="error" style={{ marginBottom: 32 }}>
              <TablerTypography variant="h6" gutterBottom>
                Fehler beim Laden der Systemdaten
              </TablerTypography>
              <TablerTypography variant="body2">
                {statusError?.message || metricsError?.message || healthError?.message}
              </TablerTypography>
            </Alert>
          </TablerContainer>
        </main>
      </>
    )
  }

  return (
    <>
      <header>
        <h1 style={{ display: 'none' }}>System Status</h1>
      </header>
              <main>
          <TablerContainer variant="page">
            {/* Page Header */}
            <TablerBox style={{ marginBottom: 32 }}>
              <TablerTypography variant="h4" component="h2" gutterBottom>
                System Status
              </TablerTypography>
              <TablerTypography variant="body1" textVariant="muted">
                Überwachung der Systemgesundheit und Performance-Metriken
              </TablerTypography>
            </TablerBox>

          {/* Overall Status Cards */}
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    {getStatusIcon(systemStatus?.status || 'unknown')}
                    <Typography variant="h6" ml={1}>
                      System Status
                    </Typography>
                  </Box>
                  <Chip
                    label={systemStatus?.status || 'Unknown'}
                    color={getStatusColor(systemStatus?.status || 'unknown')}
                    variant="filled"
                  />
                  {systemStatus?.uptime && (
                    <Typography variant="body2" color="text.secondary" mt={1}>
                      Uptime: {formatUptime(systemStatus.uptime)}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <MemoryIcon color="primary" />
                    <Typography variant="h6" ml={1}>
                      Memory Usage
                    </Typography>
                  </Box>
                  {systemMetrics?.memory && (
                    <>
                      <Typography variant="h5" color="primary">
                        {formatPercentage(systemMetrics.memory.usage_percent)}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={systemMetrics.memory.usage_percent * 100}
                        sx={{ mt: 1, mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        {formatBytes(systemMetrics.memory.used)} / {formatBytes(systemMetrics.memory.total)}
                      </Typography>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <StorageIcon color="primary" />
                    <Typography variant="h6" ml={1}>
                      Disk Usage
                    </Typography>
                  </Box>
                  {systemMetrics?.disk && (
                    <>
                      <Typography variant="h5" color="primary">
                        {formatPercentage(systemMetrics.disk.usage_percent)}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={systemMetrics.disk.usage_percent * 100}
                        sx={{ mt: 1, mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        {formatBytes(systemMetrics.disk.used)} / {formatBytes(systemMetrics.disk.total)}
                      </Typography>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Performance Metrics */}
          {systemMetrics?.performance && (
            <Card sx={{ mb: 4 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={3}>
                  <PerformanceIcon color="primary" />
                  <Typography variant="h6" ml={1}>
                    Performance Metrics
                  </Typography>
                </Box>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {systemMetrics.performance.cpu_usage_percent.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        CPU Usage
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {systemMetrics.performance.avg_response_time.toFixed(0)}ms
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Response Time
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {systemMetrics.performance.requests_per_second.toFixed(1)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Requests/sec
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {systemMetrics.performance.active_connections}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Active Connections
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Service Health */}
          {systemHealth?.services && (
            <Card sx={{ mb: 4 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={3}>
                  <MetricsIcon color="primary" />
                  <Typography variant="h6" ml={1}>
                    Service Health
                  </Typography>
                </Box>
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Service</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Response Time</TableCell>
                        <TableCell>Last Check</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                                           {Object.entries(systemHealth.services).map(([serviceName, serviceData]) => {
                       const service = serviceData as any // Type assertion für unbekannte API-Struktur
                       return (
                         <TableRow key={serviceName}>
                           <TableCell>
                             <Box display="flex" alignItems="center">
                               {getStatusIcon(service?.status || 'unknown')}
                               <Typography ml={1} fontWeight="medium">
                                 {serviceName}
                               </Typography>
                             </Box>
                           </TableCell>
                           <TableCell>
                             <Chip
                               label={service?.status || 'Unknown'}
                               color={getStatusColor(service?.status || 'unknown')}
                               size="small"
                             />
                           </TableCell>
                           <TableCell>
                             {service?.response_time ? `${service.response_time}ms` : 'N/A'}
                           </TableCell>
                           <TableCell>
                             {service?.last_check ? new Date(service.last_check).toLocaleString() : 'N/A'}
                           </TableCell>
                         </TableRow>
                       )
                     })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {/* System Information */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                {systemStatus?.version && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">
                      Version:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {systemStatus.version}
                    </Typography>
                  </Grid>
                )}
                {systemStatus?.environment && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">
                      Environment:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {systemStatus.environment}
                    </Typography>
                  </Grid>
                )}
                {systemStatus?.hostname && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">
                      Hostname:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {systemStatus.hostname}
                    </Typography>
                  </Grid>
                )}
                {systemStatus?.timestamp && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">
                      Last Updated:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {new Date(systemStatus.timestamp).toLocaleString()}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
                  </TablerContainer>
        </main>
    </>
  )
} 