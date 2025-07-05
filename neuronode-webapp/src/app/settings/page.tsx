'use client'

import {
  Science as DemoIcon,
  Cloud as ProductionIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  RestartAlt as ResetIcon,
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
  Settings as SettingsIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  SettingsBrightness as SystemIcon,
} from '@mui/icons-material'
import {
  Container,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Box,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Paper,
  Grid,
} from '@mui/material'
import { useState, useEffect } from 'react'

import { useTheme } from '@/contexts/ThemeContext'
import { useAppConfig } from '@/hooks/useAppConfig'
import { PerformanceMonitor } from '@/lib/performance'

export default function SettingsPage() {
  const {
    config,
    isDemo,
    isProduction,
    isLoading,
    switchMode,
    updateProductionUrls,
    checkHealth,
    reset
  } = useAppConfig()
  
  const { mode: themeMode, isDark, setThemeMode } = useTheme()

  const [tempApiUrl, setTempApiUrl] = useState(config.apiUrl)
  const [showSuccess, setShowSuccess] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'success' | 'error' | null>(null)

  useEffect(() => {
    // Performance Monitoring
    PerformanceMonitor.trackPageLoad('SettingsPage')
    
    setTempApiUrl(config.apiUrl)
  }, [config.apiUrl])

  const handleModeSwitch = (checked: boolean) => {
    const newMode = checked ? 'production' : 'demo'
    switchMode(newMode)
    setShowSuccess(true)
    setTimeout(() => setShowSuccess(false), 3000)
  }

  const handleApiUrlUpdate = () => {
    if (tempApiUrl !== config.apiUrl) {
      updateProductionUrls(tempApiUrl)
      setShowSuccess(true)
      setTimeout(() => setShowSuccess(false), 3000)
    }
  }

  const handleTestConnection = async () => {
    setConnectionStatus('checking')
    try {
      const healthy = await checkHealth()
      setConnectionStatus(healthy ? 'success' : 'error')
    } catch {
      setConnectionStatus('error')
    }
    setTimeout(() => setConnectionStatus(null), 5000)
  }

  const handleReset = () => {
    reset()
    setTempApiUrl('http://localhost:8000')
    setShowSuccess(true)
    setTimeout(() => setShowSuccess(false), 3000)
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          <SettingsIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Systemeinstellungen
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Konfiguration für Demo- und Produktionsmodus
        </Typography>
      </Box>

      {showSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Einstellungen erfolgreich gespeichert!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Mode Selection */}
        <Grid xs={12} md={4}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Betriebsmodus
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DemoIcon sx={{ mr: 1, color: isDemo ? 'warning.main' : 'text.disabled' }} />
                <FormControlLabel
                  control={
                    <Switch
                      checked={isProduction}
                      onChange={(e) => handleModeSwitch(e.target.checked)}
                      disabled={isLoading}
                    />
                  }
                  label=""
                  sx={{ mx: 1 }}
                />
                <ProductionIcon sx={{ ml: 1, color: isProduction ? 'primary.main' : 'text.disabled' }} />
              </Box>

              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <Chip
                  icon={isDemo ? <DemoIcon /> : <ProductionIcon />}
                  label={isDemo ? 'Demo Modus' : 'Produktions Modus'}
                  color={isDemo ? 'warning' : 'primary'}
                  variant="filled"
                />
              </Box>

              <Typography variant="body2" color="text.secondary">
                {isDemo
                  ? 'Demo-Modus nutzt synthetische Daten und simuliert alle Funktionen ohne Backend-Verbindung.'
                  : 'Produktions-Modus verbindet sich mit dem echten Backend und nutzt Ihre Daten.'
                }
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Connection Settings */}
        <Grid xs={12} md={4}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Verbindungseinstellungen
              </Typography>

              <TextField
                fullWidth
                label="API URL"
                value={tempApiUrl}
                onChange={(e) => setTempApiUrl(e.target.value)}
                disabled={isDemo}
                helperText={isDemo ? 'Im Demo-Modus nicht verfügbar' : 'Backend API Adresse'}
                sx={{ mb: 2 }}
              />

              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Button
                  variant="outlined"
                  onClick={handleApiUrlUpdate}
                  disabled={isDemo || tempApiUrl === config.apiUrl}
                  startIcon={<SaveIcon />}
                >
                  Speichern
                </Button>
                <Button
                  variant="outlined"
                  onClick={handleTestConnection}
                  disabled={isDemo}
                  startIcon={<RefreshIcon />}
                >
                  Testen
                </Button>
              </Box>

              {connectionStatus && (
                <Alert 
                  severity={connectionStatus === 'success' ? 'success' : connectionStatus === 'error' ? 'error' : 'info'}
                  sx={{ mt: 1 }}
                >
                  {connectionStatus === 'checking' && 'Verbindung wird getestet...'}
                  {connectionStatus === 'success' && 'Verbindung erfolgreich!'}
                  {connectionStatus === 'error' && 'Verbindung fehlgeschlagen!'}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Theme Settings */}
        <Grid xs={12} md={4}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Design
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, flexGrow: 1 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={themeMode === 'dark'}
                      onChange={(e) => setThemeMode(e.target.checked ? 'dark' : 'light')}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {isDark ? <DarkModeIcon /> : <LightModeIcon />}
                      <Typography>Dark Mode</Typography>
                    </Box>
                  }
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={themeMode === 'system'}
                      onChange={(e) => setThemeMode(e.target.checked ? 'system' : 'light')}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SystemIcon />
                      <Typography>System folgen</Typography>
                    </Box>
                  }
                />

                <Typography variant="body2" color="text.secondary" sx={{ mt: 'auto' }}>
                  {themeMode === 'system' 
                    ? `Folgt der Systemeinstellung (aktuell: ${isDark ? 'dunkel' : 'hell'})`
                    : `Manuell auf ${themeMode === 'dark' ? 'dunkel' : 'hell'} gesetzt`
                  }
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Systemstatus & Überwachung
              </Typography>

              <Grid container spacing={3}>
                <Grid xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Services
                  </Typography>
                  <List dense>
                    {Object.entries(config.features).map(([feature, enabled]) => (
                      <ListItem key={feature}>
                        <ListItemIcon>
                          {enabled ? 
                            <HealthyIcon color="success" /> : 
                            <ErrorIcon color="error" />
                          }
                        </ListItemIcon>
                        <ListItemText primary={feature} />
                      </ListItem>
                    ))}
                  </List>
                </Grid>

                <Grid xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Performance
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Response Time:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {isDemo ? '~1.2s' : 'N/A'}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Modus:</Typography>
                      <Chip 
                        size="small" 
                        label={isDemo ? 'Demo' : 'Produktion'} 
                        color={isDemo ? 'warning' : 'primary'} 
                      />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Theme:</Typography>
                      <Chip 
                        size="small" 
                        label={isDark ? 'Dark' : 'Light'} 
                        color="default"
                      />
                    </Box>
                  </Box>
                </Grid>

                <Grid xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Konfiguration
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                    <Typography variant="body2" component="pre" sx={{ fontSize: '0.7rem', lineHeight: 1.2 }}>
                      {JSON.stringify(config, null, 2)}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Actions */}
        <Grid xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Aktionen
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  color="warning"
                  onClick={handleReset}
                  startIcon={<ResetIcon />}
                >
                  Auf Standard zurücksetzen
                </Button>

                <Button
                  variant="outlined"
                  onClick={() => window.location.reload()}
                  startIcon={<RefreshIcon />}
                >
                  Seite neu laden
                </Button>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Änderungen werden automatisch gespeichert und sofort angewendet.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  )
} 