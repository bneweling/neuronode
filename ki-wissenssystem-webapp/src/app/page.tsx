'use client'

import { useState, useEffect } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Box,
  LinearProgress,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
  Paper,
  Divider,
} from '@mui/material'
import {
  Home as HomeIcon,
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  CloudUpload as UploadIcon,
  Menu as MenuIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,

  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material'
import ChatInterface from '@/components/chat/ChatInterface'
import GraphVisualization from '@/components/graph/GraphVisualization'
import FileUploadZone from '@/components/upload/FileUploadZone'
import { getAPIClient } from '@/lib/api'

type ViewType = 'overview' | 'chat' | 'graph' | 'upload'

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

interface NavigationItem {
  id: ViewType
  label: string
  icon: React.ElementType
  description: string
}

export default function HomePage() {
  const [currentView, setCurrentView] = useState<ViewType>('overview')
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    api: false,
    vectorStore: false,
    graphDb: false,
    lastCheck: 'Nie'
  })
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // System Status Check
  useEffect(() => {
    const checkSystemStatus = async () => {
      setIsLoading(true)
      try {
        const apiClient = getAPIClient()
        
        const health = await apiClient.healthCheck()
        setSystemStatus({
          api: health.status === 'healthy',
          vectorStore: health.components?.vector_store === 'healthy' || false,
          graphDb: health.components?.graph_db === 'healthy' || false,
          lastCheck: new Date().toLocaleTimeString('de-DE')
        })

        if (health.status === 'healthy') {
          try {
            const diag = await apiClient.getDiagnostics()
            setDiagnostics(diag)
          } catch (error) {
            console.log('Erweiterte Diagnostics nicht verfügbar:', error)
          }
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

  const navigationItems: NavigationItem[] = [
    { 
      id: 'overview', 
      label: 'Übersicht', 
      icon: HomeIcon,
      description: 'Systemstatus und Metriken'
    },
    { 
      id: 'chat', 
      label: 'KI-Chat', 
      icon: ChatIcon,
      description: 'Intelligente Unterhaltung'
    },
    { 
      id: 'graph', 
      label: 'Wissensgraph', 
      icon: GraphIcon,
      description: 'Datenvisualisierung'
    },
    { 
      id: 'upload', 
      label: 'Dokumente', 
      icon: UploadIcon,
      description: 'Datei-Management'
    },
  ]

  const handleNavigation = (viewId: ViewType) => {
    setCurrentView(viewId)
    setDrawerOpen(false)
  }

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
            <Typography variant="h4" fontWeight="bold">
              {value}{unit}
            </Typography>
          </Box>
          <Box 
            sx={{ 
              p: 1.5, 
              bgcolor: 'primary.light', 
              borderRadius: 2,
              color: 'primary.contrastText'
            }}
          >
            <Icon />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  const renderOverview = () => (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box textAlign="center" mb={6}>
        <Typography variant="h2" component="h1" gutterBottom fontWeight="light">
          KI-Wissenssystem
        </Typography>
        <Typography variant="h5" color="text.secondary" maxWidth="600px" mx="auto">
          Intelligentes Wissensmanagement mit modernster Technologie
        </Typography>
      </Box>

      {/* System Status */}
      <Card elevation={2} sx={{ mb: 4 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <Box 
              sx={{ 
                p: 1, 
                bgcolor: 'success.light', 
                borderRadius: 2,
                color: 'success.contrastText'
              }}
            >
              <ComputerIcon />
            </Box>
            <Typography variant="h5" fontWeight="medium">
              Systemstatus
            </Typography>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <StatusIndicator status={systemStatus.api} label="API-Server" />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatusIndicator status={systemStatus.vectorStore} label="Vektordatenbank" />
            </Grid>
            <Grid item xs={12} md={4}>
              <StatusIndicator status={systemStatus.graphDb} label="Graph-Datenbank" />
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />
          
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">
              Letzte Prüfung
            </Typography>
            <Typography variant="body2" fontWeight="medium">
              {systemStatus.lastCheck}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {diagnostics?.performance && (
        <Box mb={4}>
          <Typography variant="h5" fontWeight="medium" mb={3}>
            Performance-Metriken
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                title="Antwortzeit"
                value={diagnostics.performance.response_time}
                unit="ms"
                icon={SpeedIcon}
              />
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                title="Datenbanklatenz"
                value={diagnostics.performance.database_latency}
                unit="ms"
                icon={StorageIcon}
              />
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                title="Speichernutzung"
                value={diagnostics.performance.memory_usage}
                unit="%"
                icon={MemoryIcon}
              />
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <MetricCard
                title="CPU-Auslastung"
                value={diagnostics.performance.cpu_usage}
                unit="%"
                icon={ComputerIcon}
              />
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Features Grid */}
      <Box>
        <Typography variant="h5" fontWeight="medium" mb={3}>
          Funktionen entdecken
        </Typography>
        
        <Grid container spacing={3}>
          {navigationItems.slice(1).map((item) => (
            <Grid item xs={12} sm={6} lg={4} key={item.id}>
              <Card 
                elevation={2}
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    elevation: 8,
                    transform: 'translateY(-4px)'
                  }
                }}
                onClick={() => handleNavigation(item.id)}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <Box 
                      sx={{ 
                        p: 1.5, 
                        bgcolor: 'primary.light', 
                        borderRadius: 2,
                        color: 'primary.contrastText'
                      }}
                    >
                      <item.icon />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="medium">
                        {item.label}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {item.description}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box mt={2} pt={2} borderTop={1} borderColor="divider">
                    {item.id === 'chat' && (
                      <Chip 
                        icon={<CheckCircleIcon />} 
                        label="KI-Assistent bereit" 
                        color="success" 
                        size="small" 
                      />
                    )}
                    {item.id === 'graph' && (
                      <Chip 
                        label="Interaktive Visualisierung" 
                        color="primary" 
                        size="small" 
                      />
                    )}
                    {item.id === 'upload' && (
                      <Chip 
                        label="Drag & Drop Support" 
                        color="secondary" 
                        size="small" 
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  )

  const renderCurrentView = () => {
    switch (currentView) {
      case 'overview':
        return renderOverview()
      case 'chat':
        return <ChatInterface />
      case 'graph':
        return <GraphVisualization />
      case 'upload':
        return <FileUploadZone />
      default:
        return renderOverview()
    }
  }

  const drawer = (
    <List>
      {navigationItems.map((item) => (
        <ListItem key={item.id} disablePadding>
          <ListItemButton
            selected={currentView === item.id}
            onClick={() => handleNavigation(item.id)}
          >
            <ListItemIcon>
              <item.icon color={currentView === item.id ? 'primary' : 'inherit'} />
            </ListItemIcon>
            <ListItemText 
              primary={item.label}
              secondary={item.description}
            />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  )

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Navigation */}
      <AppBar position="sticky" elevation={1}>
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            KI-Wissenssystem
          </Typography>
          
          {!isMobile && (
            <Box display="flex" gap={1}>
              {navigationItems.map((item) => (
                <Button
                  key={item.id}
                  color="inherit"
                  startIcon={<item.icon />}
                  onClick={() => handleNavigation(item.id)}
                  sx={{
                    bgcolor: currentView === item.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.1)'
                    }
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
        }}
      >
        <Toolbar />
        {drawer}
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default' }}>
        {renderCurrentView()}
      </Box>

      {/* Loading Overlay */}
      {isLoading && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bgcolor="rgba(0,0,0,0.5)"
          display="flex"
          alignItems="center"
          justifyContent="center"
          zIndex={9999}
        >
          <Paper elevation={8} sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              System wird überprüft...
            </Typography>
            <LinearProgress sx={{ mt: 2, width: 200 }} />
          </Paper>
        </Box>
      )}
    </Box>
  )
}
