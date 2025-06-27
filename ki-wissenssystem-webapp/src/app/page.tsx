'use client'

import { useState, useEffect } from 'react'
import {
  Container,
  Grid,
  Card,
  CardContent,
  Box,
  Paper,
  Fade,
  Grow,
  Typography,
  Chip,
  Alert,
} from '@mui/material'
import {
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  CloudUpload as UploadIcon,
  Assessment as StatusIcon,
  School as KnowledgeIcon,
  Science as DemoIcon,
  Cloud as ProductionIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import { useRouter } from 'next/navigation'
import QuickChatInterface from '@/components/chat/QuickChatInterface'
import { useAppConfig } from '@/hooks/useAppConfig'

export default function HomePage() {
  const router = useRouter()
  const { isDemo } = useAppConfig()
  const [isMounted, setIsMounted] = useState(false)

  // Verhindere Hydration-Fehler durch Warten auf Client-Side Mount
  useEffect(() => {
    setIsMounted(true)
  }, [])

  const handleNavigation = (path: string) => {
    router.push(path)
  }

  const FeatureCard = ({ title, description, icon: Icon, onClick }: {
    title: string
    description: string
    icon: React.ElementType
    onClick: () => void
  }) => (
    <Grow in timeout={1000}>
      <Card 
        elevation={2}
        sx={{ 
          height: '100%',
          cursor: 'pointer',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            elevation: 8,
            transform: 'translateY(-4px)',
          }
        }}
        onClick={onClick}
      >
        <CardContent sx={{ textAlign: 'center', p: 3 }}>
          <Icon color="primary" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" gutterBottom fontWeight="600">
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        </CardContent>
      </Card>
    </Grow>
  )

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Mode Indicator - Nur nach Client Mount rendern */}
      {isMounted && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <Chip
            icon={isDemo ? <DemoIcon /> : <ProductionIcon />}
            label={isDemo ? 'Demo Modus' : 'Produktions Modus'}
            color={isDemo ? 'warning' : 'primary'}
            variant="filled"
            onClick={() => handleNavigation('/settings')}
            sx={{ cursor: 'pointer' }}
          />
        </Box>
      )}

      {isMounted && isDemo && (
        <Alert 
          severity="info" 
          sx={{ mb: 4, maxWidth: 800, mx: 'auto' }}
          action={
            <Chip
              icon={<SettingsIcon />}
              label="Einstellungen"
              size="small"
              onClick={() => handleNavigation('/settings')}
              sx={{ cursor: 'pointer' }}
            />
          }
        >
          Sie befinden sich im Demo-Modus. Alle Daten sind synthetisch und dienen nur zur Demonstration.
        </Alert>
      )}

      {/* Hero Section */}
      <Fade in timeout={800}>
        <Box textAlign="center" mb={6}>
          <Typography 
            variant="h2" 
            component="h1" 
            gutterBottom
            sx={{ 
              fontWeight: 300,
              background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 2
            }}
          >
            Willkommen im KI-Wissenssystem
          </Typography>
          <Typography 
            variant="h5" 
            color="text.secondary" 
            sx={{ maxWidth: 600, mx: 'auto', mb: 4, fontWeight: 300 }}
          >
            Ihr intelligenter Assistent für Wissensmanagement und Datenanalyse
          </Typography>
        </Box>
      </Fade>

      {/* Quick Chat Interface */}
      <Box mb={6} maxWidth="md" mx="auto">
        <QuickChatInterface />
      </Box>

      {/* Feature Cards - Optimiertes Layout */}
      <Box mb={6}>
        <Typography variant="h4" textAlign="center" gutterBottom sx={{ mb: 4 }}>
          Entdecken Sie die Funktionen
        </Typography>
        
        <Grid container spacing={4} justifyContent="center">
          <Grid item xs={12} sm={6} lg={3}>
            <FeatureCard
              title="KI-Chat"
              description="Stellen Sie intelligente Fragen und erhalten Sie präzise Antworten"
              icon={ChatIcon}
              onClick={() => handleNavigation('/chat')}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} lg={3}>
            <FeatureCard
              title="Wissensgraph"
              description="Visualisieren Sie Verbindungen in Ihren Daten"
              icon={GraphIcon}
              onClick={() => handleNavigation('/graph')}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} lg={3}>
            <FeatureCard
              title="Dokumente"
              description="Laden Sie Dateien hoch und verwalten Sie Ihr Wissen"
              icon={UploadIcon}
              onClick={() => handleNavigation('/upload')}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} lg={3}>
            <FeatureCard
              title="System"
              description="Überwachen Sie Performance und Systemgesundheit"
              icon={StatusIcon}
              onClick={() => handleNavigation('/status')}
            />
          </Grid>
        </Grid>
      </Box>

      {/* Info Section */}
      <Fade in timeout={1200}>
        <Paper 
          elevation={2} 
          sx={{ 
            p: 4, 
            textAlign: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }}
        >
          <KnowledgeIcon sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h5" gutterBottom fontWeight="600">
            Moderne KI-Technologie
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 600, mx: 'auto' }}>
            Nutzen Sie die Kraft von Large Language Models, Vektor-Datenbanken und 
            Graph-Technologien für intelligentes Wissensmanagement.
          </Typography>
        </Paper>
      </Fade>
    </Container>
  )
}
